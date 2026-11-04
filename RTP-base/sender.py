import argparse
import socket
import sys
import time
import select
from utils import PacketHeader, compute_checksum

def make_packet(p_type, seq_num, payload=b""):
    length = len(payload)
    pkt_header = PacketHeader(type=p_type, seq_num=seq_num, length=length, checksum=0)
    pkt_header.checksum = compute_checksum(pkt_header / payload)
    return bytes(pkt_header / payload)

def sender(receiver_ip, receiver_port, window_size):
    sever = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sever.setblocking(False)
    clinet_adr = (receiver_ip, receiver_port)

    raw_data = sys.stdin.buffer.read()
    chunks = [raw_data[i : i + 1456] for i in range(0, len(raw_data), 1456)]
    total_packets = len(chunks)

    start_pkt = make_packet(0, 0)
    while(True):
        sever.sendto(start_pkt, clinet_adr)
        ready = select.select([sever], [], [], 0.5)
        if ready[0]:
            bin_response, _ = sever.recvfrom(2048)
            if len(bin_response) >= 16:
                ack_header = PacketHeader(bin_response[:16])
                if ack_header.type == 3 and ack_header.seq_num == 1:
                    break

    count = 1  
    expected_sequence = 1  
    timer_start = time.time()

    while expected_sequence <= total_packets:
        while count < expected_sequence + window_size and count <= total_packets:
            final_message = make_packet(2, count, chunks[count - 1])
            sever.sendto(final_message, clinet_adr)
            if expected_sequence == count:
                timer_start = time.time()
            count += 1

        ready = select.select([sever], [], [], 0.01)
        if ready[0]:
            bin_response, _ = sever.recvfrom(2048)
            if len(bin_response) >= 16:
                ack_header = PacketHeader(bin_response[:16])
                response = ack_header.seq_num
                
                if ack_header.type == 3 and response > expected_sequence:
                    expected_sequence = response
                    timer_start = time.time()  


        if time.time() - timer_start > 0.5:
            for i in range(expected_sequence, count):
                final_message = make_packet(2, i, chunks[i - 1])
                sever.sendto(final_message, clinet_adr)
            timer_start = time.time()

    end_seq = total_packets + 1
    end_pkt = make_packet(1, end_seq)
    sever.sendto(end_pkt, clinet_adr)
    
    end_timer = time.time()
    while time.time() - end_timer < 0.5:
        ready = select.select([sever], [], [], 0.5 - (time.time() - end_timer))
        if ready[0]:
            bin_response, _ = sever.recvfrom(2048)
            if len(bin_response) >= 16:
                ack_header = PacketHeader(bin_response[:16])
                if ack_header.type == 3 and ack_header.seq_num == end_seq + 1:
                    break
                    
    sever.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("receiver_ip")
    parser.add_argument("receiver_port", type=int)
    parser.add_argument("window_size", type=int)
    args = parser.parse_args()
    sender(args.receiver_ip, args.receiver_port, args.window_size)

if __name__ == "__main__":
    main()