#!/usr/bin/env python
import sys
import getopt
import struct
import socket
import re

import pyrip_packet as res
from pyrip_lib import *

def broadcast_address(address,prefixlen):
    ip_value = struct.unpack('!I',socket.inet_pton(socket.AF_INET, address))[0]
    ip_value = ip_value | (0xffffffff >> prefixlen)
    return socket.inet_ntop(socket.AF_INET, struct.pack('!I',ip_value))

def show_help():
    print('pyrip.py -[hi]')
    print('{:15s} {:30s}'.format('-{}, --{}'.format('h','help'), 
            'To show all commands.'))
    print('{:15s} {:30s}'.format('-{}, --{}'.format('i','network'), 
            'Required, Enter a network. ie. 192.168.1.23/24'))

def main(argv):
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

    # verify prefix length
    prefixlen = int(prefixlen,10)
    if prefixlen > 32 or prefixlen < 0:
        print('Invalid prefix length.')
        sys.exit()

    # verify ip address
    ipv4format = r'^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){4,4}'
    if not re.match(ipv4format, address+'.'):
        print('Invalid address.')
        sys.exit()

    broadcast = broadcast_address(address, prefixlen)

    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 41600)
    try:
        sock.bind((address, 0))
    except OSError as e:
        print('OSError({0}): {1}'.format(e.errno, e.strerror))
        sys.exit()

    '''
        TODO: code below are just for test. 
        A process should be created to send update packets and 
        react to other RIP router.
    '''
    # create request packet
    rip_packet = res.RipPacket(res.RIP_COMMAND_REQUEST, 2)
    rip_packet.add_entry(0, 0, 0, 16)
    print(rip_packet)

    # send request
    sock.sendto(rip_packet.pack(),(res.RIP_MULTICAST_ADDR, 520))

    # create response packet
    rip_packet = res.RipPacket(res.RIP_COMMAND_RESPONSE, 2)
    rip_packet.add_entry(IP2INT(address), PREFIXLEN2MASK(prefixlen), 0, 1)
    print(rip_packet[0])

    # send request
    sock.sendto(rip_packet.pack(),(res.RIP_MULTICAST_ADDR, 520))

    sock.close()

if __name__ == '__main__':
    main(sys.argv[1:])