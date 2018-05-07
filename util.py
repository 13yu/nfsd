def make_fragment_header(is_last, fragment_bytes):
    n = len(fragment_bytes)
    if is_last:
        n = n | 0x80000000L

    header_bytes = (chr(int(n >> 24 & 0xff)) +
                    chr(int(n >> 16 & 0xff)) +
                    chr(int(n >> 8 & 0xff)) +
                    chr(int(n >> 0 & 0xff)))

    return header_bytes


def parse_fragment_header(header_bytes):
    v = (long(ord(header_bytes[0]) << 24) |
         ord(header_bytes[1]) << 16 |
         ord(header_bytes[2]) << 8 |
         ord(header_bytes[3]))

    is_last = (v & 0x80000000) != 0
    n = (v & 0x7fffffff)

    return is_last, n


def recv_data(sock, n):
    data = ''
    while n > 0:
        buf = sock.recv(n)
        data += buf
        n -= len(buf)

    return data
