#!/usr/bin/env python
import sys
import getopt
import struct
import socket
import re

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

from pyrip_lib import *

'''
    Provides methods to handle RIP routes
'''
class RipRouteEntry(object):
    def __init__(self, address, mask, nexthop, metric, route_tag=0, family=RIP_ADDRESS_FAMILY):
        self.family = family
        self.route_tag = route_tag
        self.address = address
        self.mask = mask
        self.nexthop = nexthop
        self.metric = metric

    def pack(self):
        return struct.pack(RIP_ENTRY_PACK_FORMAT,self.family,self.route_tag,self.address,self.mask,self.nexthop,self.metric)

    def __repr__(self):
        return '{:}/{:d}: {:} ({:d})'.format(ipaddr.ip_address(self.address),Mask2PrefixLen(self.mask),ipaddr.ip_address(self.nexthop),self.metric)

'''
    Provides methods to handle RIP packets
'''
class RipPacket(object):
    def __init__(self, cmd = RIP_COMMAND_RESPONSE, version = 2):
        self.command = cmd
        self.version = version

        self.entry = []
        return

    @property
    def size(self):
        return RIP_HEADER_SIZE + len(self.entry)*RIP_ENTRY_SIZE

    def add_entry(self, network=None, address=None, mask=None, nexthop=None, metric=0, family=2, route_tag=0):
        if not network is None:
            address = int(network.network_address)
            mask = int(network.netmask)

        if not (type(address) is int and 
                type(mask) is int and 
                type(nexthop) is int):
            return False

        self.entry.append(RipRouteEntry(address, mask, nexthop, metric, route_tag, family))
        return True

    def remove_entry(self, address, mask, nexthop):
        for ent in self.entry:
            if ent.address == ip_addr:
                self.entry.remove(ent)
                return True
        return False
    def __getitem__(self, key):
        return self.entry[key]

    def pack(self):
        header = struct.pack(RIP_HEADER_PACK_FORMAT,self.command,self.version,0)
        entries = b''
        for ent in self.entry:
            entries = entries + ent.pack()
        packet = header + entries
        return packet

    def unpack(self, data):
        hdr = data[:RIP_HEADER_SIZE]
        data = data[RIP_HEADER_SIZE:]
        self.command, self.version, zero = struct.unpack(RIP_HEADER_PACK_FORMAT, hdr)
        while len(data) > 0 and len(data)%RIP_ENTRY_SIZE == 0:
            ent = data[:RIP_ENTRY_SIZE]
            data = data[RIP_ENTRY_SIZE:]
            family, tag, address, mask, nexthop, metric = struct.unpack(RIP_ENTRY_PACK_FORMAT, ent)
            self.entry.append(RipRouteEntry(address, mask, nexthop, metric, tag, family))

        return

    def __repr__(self):
        if self.command == RIP_COMMAND_REQUEST:
            cmd = 'request'
        elif self.command == RIP_COMMAND_RESPONSE:
            cmd = 'response'

        ret = 'v{:d}, {:s}, {:d} entries'.format(self.version,cmd,len(self.entry))
        return ret

'''
    main RIP process. RIP version 2.
    version 1 should be added in future.
'''
class RIP(DatagramProtocol):
    def __init__(self):
        self.ttl = 1 # link-local. Not going to follow history ttl=2.
        #
        reactor.callLater(RIP_DEFAULT_UPDATE, self.sendRegularUpdate)

    def startProtocol(self):
        self.transport.setTTL(self.ttl)
        self.transport.joinGroup(RIP_MULTICAST_ADDR)
        self.transport.setLoopbackMode(False)
        self.transport.setBroadcastAllowed(True)
        #
        self.requestAllRoutes()

    def datagramReceived(self, datagram, address):
        print('Datagram received from {}'.format(repr(address)))
        # handle received packets
        # decodePacket(datagram)

    def connectionRefused(self):
        pass

    def sendRegularUpdate(self):
        # construct update packet
        #self.transport.write(msg, ('<broadcast>', RIP_UDP_PORT))
        reactor.callLater(RIP_DEFAULT_UPDATE, self.sendRegularUpdate)

    def sendRequest(self, route):
        # construct request packet
        pass

    def requestAllRoutes(self):
        pkt = RipPacket(RIP_COMMAND_REQUEST, 2)
        pkt.add_entry(
            family = 0, 
            route_tag = 0, 
            address = 0, 
            mask = 0, 
            nexthop = 0, 
            metric = 16)
        self.transport.write(pkt.pack(), (RIP_MULTICAST_ADDR, RIP_UDP_PORT))

def main(argv):
    reactor.listenMulticast(RIP_UDP_PORT, RIP(), listenMultiple=True)
    reactor.run()

if __name__ == '__main__':
    main(sys.argv[1:])