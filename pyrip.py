#!/usr/bin/env python
import sys
import getopt
import struct
import socket
import ipaddress as ipaddr
import re

import pyrip_timer as timer
import pyrip_interface as iface
import pyrip_packet as pkt
from pyrip_lib import *

rip_running = False
rip_interfaces = {}
rip_timer = {}

def request_all_packet():
    # create request packet
    rip_packet = pkt.RipPacket(pkt.RIP_COMMAND_REQUEST, 2)
    rip_packet.add_entry(
        family = 0, 
        route_tag = 0, 
        address = 0, 
        mask = 0, 
        nexthop = 0, 
        metric = 16)
    print(rip_packet)
    return rip_packet

def show_help():
    print('pyrip.py -[hi]')
    print('{:15s} {:30s}'.format('-{}, --{}'.format('h','help'), 
            'To show all commands.'))
    print('{:15s} {:30s}'.format('-{}, --{}'.format('i','network'), 
            'Required, Enter a network. ie. 192.168.1.23/24'))

def rip_init():
    global rip_running, rip_interfaces, rip_timer

    rip_running = True
    pkt = request_all_packet()

    for net, rif in rip_interfaces.items():
        rif.socket_open()
        rif.send_multicast(pkt.pack())
    rip_timer['update'] = timer.Timer(RIP_DEFAULT_UPDATE)

def rip_update():
    global rip_running, rip_interfaces, rip_timer

    # check if we received anything
    # for net, rif in rip_interfaces.items():
    #     data = rif.recv()
    #     if len(data) > 0:
    #         rv = pkt.RipPacket()
    #         rv.unpack()
    #         print(data)

    # check update timer
    if rip_timer['update'].is_expired:
        # create response packet
        rip_packet = pkt.RipPacket(pkt.RIP_COMMAND_RESPONSE, 2)
        network30 = ipaddr.ip_network('172.16.30.0/24', False)
        rip_packet.add_entry(network=network30, nexthop=0, metric=1)
        print(rip_packet)
        print(rip_packet[0])
        for net, rif in rip_interfaces.items():
            rif.send_multicast(rip_packet.pack())
        rip_timer['update'].reset()

def rip_clean():
    global rip_running, rip_interfaces, rip_timer

    for net, rif in rip_interfaces.items():
        rif.socket_close()

def main(argv):
    global rip_running, rip_interfaces, rip_timer

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

    rip_interfaces[network] = iface.RipInterface(address, network)

    # '''
    #     TODO: code below are just for test. 
    #     A process should be created to send update packets and 
    #     react to other RIP router.
    # '''

    rip_init()
    while rip_running:
        rip_update()
    rip_clean()

if __name__ == '__main__':
    main(sys.argv[1:])