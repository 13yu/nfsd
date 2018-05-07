import xdrlib

NFS3_OK = 0
NF3REG = 1
NF3DIR = 2

def proc_null(args_unpacker):
    args_unpacker.done()
    return ''

def proc_fsinfo(args_unpacker):
    fsroot = args_unpacker.unpack_opaque()
    args_unpacker.done()

    packer = xdrlib.Packer()

    packer.pack_enum(NFS3_OK)

    # attributes_follow
    packer.pack_bool(True)

    # fattr3

	# ftype3     type;
    packer.pack_enum(NF3DIR)

	# mode3      mode;
    # typedef uint32 mode3;
    packer.pack_uint(0644)

	# uint32     nlink;
    packer.pack_uint(1)

	# uid3       uid;
    # typedef uint32 uid3;
    packer.pack_uint(0)

	# gid3       gid;
    #typedef uint32 gid3;
    packer.pack_uint(0)

	# size3      size;
    # typedef uint64 size3;
    packer.pack_uhyper(4096)

	# size3      used;
    packer.pack_uhyper(4096)

	# specdata3  rdev;
    # struct specdata3 {
    #     uint32     specdata1;
    #     uint32     specdata2;
    # };
    packer.pack_uint(0)
    packer.pack_uint(0)

	# uint64     fsid;
    packer.pack_uhyper(0)

	# fileid3    fileid;
    # typedef uint64 fileid3;
    packer.pack_uhyper(0)

	# nfstime3   atime;
    # struct nfstime3 {
    #    uint32   seconds;
    #    uint32   nseconds;
    # };
    packer.pack_uint(1522116040)
    packer.pack_uint(0)

	# nfstime3   mtime;
    packer.pack_uint(1522116040)
    packer.pack_uint(0)

	# nfstime3   ctime;
    packer.pack_uint(1522116040)
    packer.pack_uint(0)

    # uint32    rtmax;
    packer.pack_uint(1024)

	# uint32    rtpref;
    packer.pack_uint(1024)

	# uint32    rtmult;
    packer.pack_uint(1)

	# uint32    wtmax;
    packer.pack_uint(1024)

	# uint32    wtpref;
    packer.pack_uint(1024)

	# uint32    wtmult;
    packer.pack_uint(1)

	# uint32    dtpref;
    packer.pack_uint(1024)

    # size3     maxfilesize;
    packer.pack_uint(1024 * 1024 * 1024)

    # nfstime3  time_delta;
    packer.pack_uint(1)
    packer.pack_uint(0)

    # uint32    properties;
    packer.pack_uint(1)

    resp = packer.get_buffer()
    return resp

procs = {
    0: proc_null,
    19: proc_fsinfo,
}

def do_call(to_call):
    proc = procs[to_call['proc']]
    resp = proc(to_call['args_unpacker'])

    return resp
