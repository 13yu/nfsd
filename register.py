import socket

import rpc_util

PMAP_PROG = 100000
PMAP_VERS = 2
PMAP_PORT = 111

# Procedure numbers
PMAPPROC_SET = 1                        # (mapping) -> bool
PMAPPROC_UNSET = 2                      # (mapping) -> bool


def pack_pmap(packer, pmap):
    prog, vers, prot, port = pmap
    packer.pack_uint(prog)
    packer.pack_uint(vers)
    packer.pack_uint(prot)
    packer.pack_uint(port)


def unpack_uint(unpacker):
    return unpacker.unpack_uint()


def register(mapping):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', PMAP_PORT))

    to_call = {
        'prog': PMAP_PROG,
        'vers': PMAP_VERS,
        'proc': PMAPPROC_UNSET,
        'args': mapping,
    }

    kwargs = {
        'args_pack_func': pack_pmap,
        'result_unpack_func': unpack_uint,
    }

    result = rpc_util.rpc_call(sock, to_call, **kwargs)
    if result != 1:
        raise UnsetMapError()

    to_call['proc'] = PMAPPROC_SET

    result = rpc_util.rpc_call(sock, to_call, **kwargs)
    if result != 1:
        raise SetMapError()

    sock.close()
    return result
