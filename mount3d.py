import xdrlib

MNT3_OK = 0

def proc_null(args_unpacker):
    args_unpacker.done()
    return ''


def proc_mnt(args_unpacker):
    dirpath = args_unpacker.unpack_string()
    args_unpacker.done()

    packer = xdrlib.Packer()
    packer.pack_enum(MNT3_OK)
    packer.pack_opaque('3' * 64)
    packer.pack_int(0)

    resp = packer.get_buffer()
    return resp


procs = {
    0: proc_null,
    1: proc_mnt,
}

def do_call(to_call):
    proc = procs[to_call['proc']]
    resp = proc(to_call['args_unpacker'])

    return resp
