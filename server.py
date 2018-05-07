import binascii
import random
import time
import socket
import sys
import xdrlib

import mount3d
import nfs3d
import register
import rpc_util
from pykit import threadutil

CALL = 0
REPLY = 1
RPCVERSION = 2
MSG_ACCEPTED = 0

SUCCESS = 0
# Port mapper interface

# Program number, version and (fixed!) port number
PMAP_PROG = 100000
PMAP_VERS = 2
PMAP_PORT = 111

# Procedure numbers
PMAPPROC_NULL = 0                       # (void) -> void
PMAPPROC_SET = 1                        # (mapping) -> bool
PMAPPROC_UNSET = 2                      # (mapping) -> bool
PMAPPROC_GETPORT = 3                    # (mapping) -> unsigned int
PMAPPROC_DUMP = 4                       # (void) -> pmaplist
PMAPPROC_CALLIT = 5                     # (call_args) -> call_result

IPPROTO_TCP = 6
IPPROTO_UDP = 17


def make_call(to_call, **kwargs):
    packer = xdrlib.Packer()

    xid = random.randint(0, 1024 * 1024)
    packer.pack_uint(xid)

    packer.pack_enum(CALL)
    packer.pack_uint(RPCVERSION)
    packer.pack_uint(to_call['prog'])
    packer.pack_uint(to_call['vers'])
    packer.pack_uint(to_call['proc'])

    cred = kwargs.get('cred', (0, ''))
    packer.pack_enum(cred[0])
    packer.pack_opaque(cred[1])

    verf = kwargs.get('verf', (0, ''))
    packer.pack_enum(verf[0])
    packer.pack_opaque(verf[1])

    if kwargs.get('args_pack_func') is not None:
        kwargs['args_pack_func'](packer, to_call['args'])

    data = packer.get_buffer()

    return xid, data


def rpc_call(sock, to_call, **kwargs):
    xid, data = make_call(to_call, **kwargs)

    resp_data = rpc_request(sock, data)

    unpacker = xdrlib.Unpacker(resp_data)

    resp_xid = unpacker.unpack_uint()
    if resp_xid != xid:
        raise XIDError('resp xid: %d is not:  %d' % (resp_xid, xid))

    msg_type = unpacker.unpack_enum()
    if msg_type != REPLY:
        raise MsgTypeError('resp msg type: %s is not REPLY' % msg_type)

    reply_stat = unpacker.unpack_enum()
    if reply_stat != MSG_ACCEPTED:
        raise DeniedError('Denied')

    verf = (unpacker.unpack_enum(), unpacker.unpack_opaque())

    accept_stat = unpacker.unpack_enum()

    if accept_stat != SUCCESS:
        raise NotSuccessError('accept_stat: %s, is not SUCCESS' % accept_stat)

    if kwargs.get('result_unpack_func') is not None:
        result = kwargs['result_unpack_func'](unpacker)
    else:
        result = None

    return result


def pack_pmap(packer, pmap):
    prog, vers, prot, port = pmap
    packer.pack_uint(prog)
    packer.pack_uint(vers)
    packer.pack_uint(prot)
    packer.pack_uint(port)


def unpack_uint(unpacker):
    return unpacker.unpack_uint()


def service_loop(port, do_call):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', port))
    sock.listen(10)

    while True:
        conn = sock.accept()

        while True:
            session = {}
            try:
                message = rpc_util.receive_message(conn[0])
                session['message'] = binascii.hexlify(message)

                xid, to_call = rpc_util.parse_call(message)
                session['to_call'] = to_call

                resp = do_call(to_call)
                session['resp'] = binascii.hexlify(resp)

                reply = rpc_util.make_reply(xid, resp)
                session['reply'] = binascii.hexlify(reply)

                conn[0].send(reply)

            except Exception as e:
                session['error'] = repr(e)
                conn[0].close()
                break

            finally:
                print 'session-------: %s' % session
                print ''

        time.sleep(3)


def mountd():
    service_loop(5555, mount3d.do_call)


def nfsd():
    service_loop(2049, nfs3d.do_call)


def run():
    try:
        register.register((100003, 3, IPPROTO_TCP, 2049))
        register.register((100005, 3, IPPROTO_TCP, 5555))

        th_mountd = threadutil.start_daemon_thread(mountd)
        th_nfsd = threadutil.start_daemon_thread(nfsd)

        th_mountd.join()
        th_nfsd.join()

    except KeyboardInterrupt:
        sys.exit(0)

run()
