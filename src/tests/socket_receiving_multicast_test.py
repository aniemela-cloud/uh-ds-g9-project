#EXAMPLE USE:
#python3 receiver.py -mc_address 224.0.2.15:65435

import struct
from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM, inet_aton, IPPROTO_IP, \
    IP_ADD_MEMBERSHIP, INADDR_ANY, SOL_SOCKET, SO_REUSEADDR
# define command line interface
parser = ArgumentParser(description='UDP Multicast Receiver')
parser.add_argument('-mc_address', help='Multicast address')
# parse command line options
args = parser.parse_args()

# create a UDP socket
with socket(AF_INET, SOCK_DGRAM) as receiver_socket:
    # on the socket level, set the ability to reuse address
    receiver_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    # bind the socket to the receiver's own address and port
    multicast_ip = args.mc_address.split(':')[0]
    multicast_port = args.mc_address.split(':')[1]
    receiver_socket.bind((multicast_ip, int(multicast_port)))
    # set up the multicast group membership by converting addresses to
    # 4sl (4 byte string and 4 byte long integer)
    multicast_request = struct.pack("4sl", inet_aton(multicast_ip), INADDR_ANY)
    # join the multicast group
    receiver_socket.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, multicast_request)
    print(f'Receiver listening on {multicast_ip}:{multicast_port}')
    # receive messages (in this case, indefinitely until interrupted)
    data, sender_address = receiver_socket.recvfrom(1024)  # Buffer size 1024 bytes
    print(f'Received message from {sender_address[0]}:{sender_address[1]}')