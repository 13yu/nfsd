import socket
import binascii
import dpkt


def inet_to_str(inet):
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)


interest_ports = [2049, 5555]


def is_interest(src_ip, src_port, dst_ip, dst_port):
    if src_port not in interest_ports and dst_port not in interest_ports:
        return False

    return True

def call_back_func(message):
    return

def analyse(packet_bytes):
    eth = dpkt.ethernet.Ethernet(packet_bytes)
    ip = eth.data

    if ip.p != 6: # 6 is tcp
        return

    tcp = ip.tcp

    src_ip = inet_to_str(ip.src)
    src_port = tcp.sport

    dst_ip = inet_to_str(ip.dst)
    dst_port = tcp.dport

    if not is_interest(src_ip, src_port, dst_ip, dst_port):
        return

    print '%s %d ----> %s %d' % (src_ip, src_port, dst_ip, dst_port)

    ip_payload = packet_bytes[14 + ip.hl * 4 : 14 + ip.len]
    tcp_payload = ip_payload[tcp.off * 4 : ]

    print binascii.hexlify(tcp_payload)
    print repr(tcp_payload)

    call_back_func(tcp_payload)

    print ''


def sniff():
    # sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))

    while True:
        data = sock.recvfrom(1024 * 1024)
        analyse(data[0])

if __name__ == '__main__':
    sniff()
