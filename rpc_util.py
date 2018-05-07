import random
import xdrlib
import binascii

import util

CALL = 0
REPLY = 1
RPCVERSION = 2
MSG_ACCEPTED = 0

AUTH_NULL = 0

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


class XIDError(Exception):
    pass


class DeniedError(Exception):
    pass


class MsgTypeError(Exception):
    pass


class NotSuccessError(Exception):
    pass


class RpcVersionError(Exception):
    pass


class FragmentError(Exception):
    pass


class FragmentHeaderError(Exception):
    pass


def receive_message(sock):
    message = ''

    while True:
        fragment_header = sock.recv(4)
        if len(fragment_header) != 4:
            raise FragmentHeaderError('fragment header: %s(%d) is invalid' %
                                      (binascii.hexlify(fragment_header),
                                       len(fragment_header)))

        is_last, n = util.parse_fragment_header(fragment_header)

        fragment = util.recv_data(sock, n)
        if len(fragment) != n:
            raise FragmentError('fragment length: %d is not: %d' %
                                (len(fragment), n))

        message += fragment
        if is_last:
            break

    return message


def rpc_request(sock, data):
    fragment_header = util.make_fragment_header(True, data)
    sock.send(fragment_header + data)

    return receive_message(sock)


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


def parse_call(message):
    unpacker = xdrlib.Unpacker(message)
    xid = unpacker.unpack_uint()

    msg_type = unpacker.unpack_enum()
    if msg_type != CALL:
        raise MsgTypeError('message type is not CALL')

    rpcvers = unpacker.unpack_uint()
    if rpcvers != RPCVERSION:
        raise RpcVersionError('rpc version is not 2')

    prog = unpacker.unpack_uint()
    vers = unpacker.unpack_uint()
    proc = unpacker.unpack_uint()

    cred = (unpacker.unpack_enum(), unpacker.unpack_opaque())
    verf = (unpacker.unpack_enum(), unpacker.unpack_opaque())

    to_call = {
        'prog': prog,
        'vers': vers,
        'proc': proc,
        'args_unpacker': unpacker,
    }

    return xid, to_call


def make_reply(xid, resp):
    packer = xdrlib.Packer()

    packer.pack_uint(xid)
    packer.pack_enum(REPLY)
    packer.pack_enum(MSG_ACCEPTED)

    packer.pack_enum(AUTH_NULL)
    packer.pack_opaque('')

    packer.pack_enum(SUCCESS)

    data = packer.get_buffer() + resp

    fragment_header = util.make_fragment_header(True, data)
    reply = fragment_header + data

    return reply
