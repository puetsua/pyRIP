#!/usr/bin/env python
import sys
import getopt
import struct
import socket
import random

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

from pyrip_lib import *

'''
    Provides methods to handle RIP routes
'''
class RipRouteEntry(object):
    def __init__(self, prefix, prefixLen, nextHop, metric, routeTag, family=RIP_ADDRESS_FAMILY):
        self.family = family
        self.routeTag = routeTag
        self.prefix = prefix
        self.prefixLen = prefixLen
        self.nextHop = nextHop
        self.metric = metric

    def pack(self):
        mask = PrefixLen2MaskInt(self.prefixLen)
        return struct.pack(RIP_ENTRY_PACK_FORMAT,
            self.family, self.routeTag, self.prefix, mask, self.nextHop, self.metric)

    def __repr__(self):
        return '{:}/{:d}: {:} ({:d})'.format(Int2IP(self.prefix), self.prefixLen, Int2IP(self.nextHop), self.metric)

'''
    Provides methods to handle RIP packets
'''
class RipPacket(object):
    def __init__(self, cmd = RIP_COMMAND_RESPONSE, version = 2):
        self.command = cmd
        self.version = version
        self.entry = []

    @property
    def size(self):
        return RIP_HEADER_SIZE + len(self.entry)*RIP_ENTRY_SIZE

    def pack(self):
        header = struct.pack(RIP_HEADER_PACK_FORMAT,self.command,self.version,0)
        entries = b''
        for ent in self.entry:
            entries = entries + ent.pack()
        packet = header + entries
        return packet

    def unpack(data):
        pkt = RipPacket()
        hdr = data[:RIP_HEADER_SIZE]
        data = data[RIP_HEADER_SIZE:]
        pkt.command, pkt.version, zero = struct.unpack(RIP_HEADER_PACK_FORMAT, hdr)
        while len(data) > 0 and len(data)%RIP_ENTRY_SIZE == 0:
            ent = data[:RIP_ENTRY_SIZE]
            data = data[RIP_ENTRY_SIZE:]
            family, tag, prefix, mask, nextHop, metric = struct.unpack(RIP_ENTRY_PACK_FORMAT, ent)
            pkt.entry.append(RipRouteEntry(
                prefix, MaskInt2PrefixLen(mask), nextHop, metric, tag, family))
        return pkt

    def addEntry(self, prefix, prefixLen, nextHop, metric, routeTag=0, family=RIP_ADDRESS_FAMILY):
        self.entry.append(RipRouteEntry(prefix, prefixLen, nextHop, metric, routeTag, family))
        return True

    def removeEntry(self, prefix, prefixLen, nextHop):
        for ent in self.entry:
            if ent.address == ip_addr:
                self.entry.remove(ent)
                return True
        return False

    def __getitem__(self, key):
        return self.entry[key]

    def __setitem__(self, key, value):
        self.entry[key] = value

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
        self.updateTime = RIP_DEFAULT_UPDATE
        self.jitterScale = RIP_DEFAULT_JITTER_SCALE
        self.loadConfigurationFile()

    ''' Twisted Functions '''
    def startProtocol(self):
        self.transport.setTTL(self.ttl)
        self.transport.joinGroup(RIP_MULTICAST_ADDR)
        self.transport.setLoopbackMode(False)
        self.transport.setBroadcastAllowed(True)
        #
        self.requestAllRoutes()
        reactor.callLater(self.getUpdateTime(), self.sendRegularUpdate)

    def datagramReceived(self, datagram, address):
        pkt = RipPacket.unpack(datagram)
        print('r', pkt, repr(address))

    def connectionRefused(self):
        pass

    ''' RIP Functions '''
    def loadConfigurationFile(self):
        pass

    def getUpdateTime(self):
        return self.updateTime + (random.random()*2-1)*self.updateTime*self.jitterScale

    def sendRegularUpdate(self):
        pkt = RipPacket(RIP_COMMAND_RESPONSE, 2)
        pkt.addEntry(IP2Int('172.16.30.0'), 24, 0, 1) # TODO
        print('s', pkt, pkt.size)
        self.transport.write(pkt.pack(), (RIP_MULTICAST_ADDR, RIP_UDP_PORT))
        reactor.callLater(self.getUpdateTime(), self.sendRegularUpdate)

    def sendRequest(self, route):
        # construct request packet
        pass

    def requestAllRoutes(self):
        pkt = RipPacket(RIP_COMMAND_REQUEST, 2)
        pkt.addEntry(
            prefix = 0, 
            prefixLen = 0,
            nextHop = 0, 
            metric = 16,
            family = 0, 
            routeTag = 0)
        print('s', pkt)
        self.transport.write(pkt.pack(), (RIP_MULTICAST_ADDR, RIP_UDP_PORT))

def main(argv):
    reactor.listenMulticast(RIP_UDP_PORT, RIP(), listenMultiple=True)
    reactor.run()

if __name__ == '__main__':
    main(sys.argv[1:])