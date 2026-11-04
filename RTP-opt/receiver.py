import argparse
import socket
import sys
from utils import PacketHeader, compute_checksum

def receiver(receiver_ip, receiver_port, window_size):
    sever = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sever.bind((receiver_ip, receiver_port))

    buffer = {}
    expected_sequence = 1
    connected = False

    while(True):
        data, clinet_adr = sever.recvfrom(2048)
        
        if len(data) < 16:
            continue

        pkt_header = PacketHeader(data[:16])
        message = data[16 : 16 + pkt_header.length]

        pkt_checksum = pkt_header.checksum
        pkt_header.checksum = 0
        computed_checksum = compute_checksum(pkt_header / message)
        if pkt_checksum != computed_checksum:
            continue

        seq_num = pkt_header.seq_num
        p_type = pkt_header.type

        if p_type == 0: 
            connected = True
            ack_pkt = PacketHeader(type=3, seq_num=1, length=0, checksum=0)
            sever.sendto(bytes(ack_pkt), clinet_adr)
            continue
            
        if not connected:
            continue

        if p_type == 2: 
            # PART 3 (INDIVIDUAL ACK): Trả đúng seq_num
            ack_pkt = PacketHeader(type=3, seq_num=seq_num, length=0, checksum=0)
            sever.sendto(bytes(ack_pkt), clinet_adr)

            if seq_num == expected_sequence:
                sys.stdout.buffer.write(message)
                expected_sequence += 1
                while expected_sequence in buffer:
                    stored_msg = buffer.pop(expected_sequence)
                    sys.stdout.buffer.write(stored_msg)
                    expected_sequence += 1
                sys.stdout.flush()
            elif seq_num > expected_sequence :
                if seq_num not in buffer:
                    buffer[seq_num] = message

        elif p_type == 1: 
            ack_pkt = PacketHeader(type=3, seq_num=seq_num + 1, length=0, checksum=0)
            sever.sendto(bytes(ack_pkt), clinet_adr)
            break

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("receiver_ip")
    parser.add_argument("receiver_port", type=int)
    parser.add_argument("window_size", type=int)
    args = parser.parse_args()
    receiver(args.receiver_ip, args.receiver_port, args.window_size)

if __name__ == "__main__":
    main()