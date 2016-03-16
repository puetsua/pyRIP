#!/usr/bin/env python
import sys
import getopt
import struct
import socket
import ipaddress as ipaddr
import re

import pyrip_packet as res
from pyrip_lib import *

def request_all_from_neighbor(sock):
    # create request packet
    rip_packet = res.RipPacket(res.RIP_COMMAND_REQUEST, 2, 0)
    rip_packet.add_entry(address=0, mask=0, nexthop=0, metric=16)
    print(rip_packet)

    # send request
    sock.sendto(rip_packet.pack(),(res.RIP_MULTICAST_ADDR, 520))

def show_help():
    print('pyrip.py -[hi]')
    print('{:15s} {:30s}'.format('-{}, --{}'.format('h','help'), 
            'To show all commands.'))
    print('{:15s} {:30s}'.format('-{}, --{}'.format('i','network'), 
            'Required, Enter a network. ie. 192.168.1.23/24'))

def main(argv):
    if len(argv) == 0:
        show_help()
        sys.exit()

    try:
        opts, args = getopt.getopt(argv,'hi:',['help','network='])
    except getopt.GetoptError:
        show_help()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            show_help()
            sys.exit()
        elif opt in ('-i', '--network'):
            network = arg

    if network == None:
        show_help()
        sys.exit()

    try:
        address, prefixlen = network.split('/');
    except ValueError:
        print('Invalid network format.')
        sys.exit()

    address = ipaddr.ip_address(address)
    network = ipaddr.ip_network(network, False)

    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 41600)
    try:
        sock.bind((str(address), RIP_UDP_PORT))
    except OSError as e:
        print('OSError({0}): {1}'.format(e.errno, e.strerror))
        sys.exit()

    # '''
    #     TODO: code below are just for test. 
    #     A process should be created to send update packets and 
    #     react to other RIP router.
    # '''

    request_all_from_neighbor(sock)

    # create response packet
    rip_packet = res.RipPacket(res.RIP_COMMAND_RESPONSE, 2)
    network30 = ipaddr.ip_network('172.16.30.0/24', False)
    rip_packet.add_entry(network=network30, nexthop=0, metric=1)
    print(rip_packet)
    print(rip_packet[0])

    # send request
    sock.sendto(rip_packet.pack(),(res.RIP_MULTICAST_ADDR, 520))

    sock.close()

if __name__ == '__main__':
    main(sys.argv[1:])