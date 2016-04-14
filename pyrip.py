#!/usr/bin/env python
import sys
import getopt
import struct
import socket
import random
import json

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

from pyrip_lib import *

'''
    Provides methods to handle RIP routes
'''
class IRoute(object):
    def __init__(self, prefix=0, prefixLen=0, nextHop=0, afi=0):
        self.afi = afi
        self.prefix = prefix
        self.prefixLen = prefixLen
        self.nextHop = nextHop

    def __cmp__(self, other):
        if self.afi < other.afi:
            return -1
        elif self.afi > other.afi:
            return 1

        if self.prefix < other.prefix:
            return -1
        elif self.prefix > other.prefix:
            return 1

        if self.prefixLen < other.prefixLen:
            return -1
        elif self.prefixLen > other.prefixLen:
            return 1

        if self.nextHop < other.nextHop:
            return -1
        elif self.nextHop > other.nextHop:
            return 1

        return 0

    def __lt__(self, other):
        return self.__cmp__(other)<0
    def __le__(self, other):
        return self.__cmp__(other)<=0
    def __eq__(self, other):
        return self.__cmp__(other)==0
    def __ne__(self, other):
        return self.__cmp__(other)!=0
    def __gt__(self, other):
        return self.__cmp__(other)>0
    def __ge__(self, other):
        return self.__cmp__(other)>=0

class RipRoute(IRoute):
    def __init__(self, prefix, prefixLen, nextHop, metric=RIP_METRIC_MIN, routeTag=0, family=RIP_ADDRESS_FAMILY):
        self.family = family
        self.routeTag = routeTag
        self.prefix = prefix
        self.prefixLen = prefixLen
        self.nextHop = nextHop
        self.afi = 1 # IPv4
        
        if metric >= RIP_METRIC_INFINITY:
            self.metric = RIP_METRIC_INFINITY
        elif metric <= RIP_METRIC_MIN:
            self.metric = RIP_METRIC_MIN
        else:
            self.metric = metric
        
    def pack(self):
        mask = PrefixLen2MaskInt(self.prefixLen)
        return struct.pack(RIP_ENTRY_PACK_FORMAT,
            self.family, self.routeTag, self.prefix, mask, self.nextHop, self.metric)

    def __str__(self):
        return '{'+'{:s}/{:d}, {:s}, {:d}, {:d}'.format(Int2IP(self.prefix), self.prefixLen, Int2IP(self.nextHop), self.metric, self.routeTag)+'}'

    def __repr__(self):
        return '{:08x}/{:d}->{:08x} m{:d} t{:d}'.format(self.prefix, self.prefixLen, self.nextHop, self.metric, self.routeTag)

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
            pkt.entry.append(RipRoute(
                prefix, MaskInt2PrefixLen(mask), nextHop, metric, tag, family))
        return pkt

    def addEntry(self, prefix, prefixLen, nextHop, metric, routeTag=0, family=RIP_ADDRESS_FAMILY):
        self.entry.append(RipRoute(prefix, prefixLen, nextHop, metric, routeTag, family))
        return True

    def removeEntry(self, prefix, prefixLen, nextHop):
        for ent in self.entry:
            if ent.prefix == prefix and ent.prefixLen == prefixLen and ent.nextHop == nextHop:
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
    def __init__(self, inputDict):
        self.ttl = 1 # link-local. Not going to follow history ttl=2.
        self.updateTime = RIP_DEFAULT_UPDATE
        self.jitterScale = RIP_DEFAULT_JITTER_SCALE
        self.RIB = []
        self.loadConfigurationFile(inputDict['configFileName'])

    ''' Twisted Functions '''
    def startProtocol(self):
        self.transport.setTTL(self.ttl)
        self.transport.joinGroup(RIP_MULTICAST_ADDR)
        self.transport.setLoopbackMode(False)
        self.transport.setBroadcastAllowed(True)
        #
        self.requestAllRoutes()
        reactor.callLater(self.getUpdateTime(), self.sendRegularUpdate)

    def datagramReceived(self, datagram, addrPort):
        pkt = RipPacket.unpack(datagram)
        print('r', pkt, repr(addrPort))

        # we only deal with RIPv2 now.
        if pkt.version != 2:
            return

        if pkt.command == RIP_COMMAND_REQUEST:
            self.respondToRequest(pkt.entry, addrPort[0])
        elif pkt.command == RIP_COMMAND_RESPONSE: 
            self.updateRIB(pkt.entry, addrPort[0])

    def connectionRefused(self):
        pass

    ''' RIP Functions '''
    def loadConfigurationFile(self, filename):
        with open(filename, 'r') as f:
            conf = json.load(f)

        if 'updateTimer' in conf:
            self.updateTime = conf['updateTimer']
        if 'routes' in conf:
            for r in conf['routes']:
                if set(('prefix', 'prefixLen', 'nextHop')) <= set(r.keys()):
                    prefix = IP2Int(r['prefix'])
                    prefixLen = r['prefixLen']
                    nextHop = IP2Int(r['nextHop'])
                    metric = RIP_METRIC_MIN if 'metric' not in r.keys() else r['metric']
                    rtag = 0 if 'routeTag' not in r.keys() else r['routeTag']
                    self.addRouteToRIB(RipRoute(prefix, prefixLen, nextHop, metric, rtag))

    def getUpdateTime(self):
        return self.updateTime + (random.random()*2-1)*self.updateTime*self.jitterScale

    # TODO
    def respondToRequest(self, routes, addr):
        # use unicast to respond
        pass

    def updateRIB(self, routes, addr):
        for r in routes:
            if r.nextHop == 0:
                r.nextHop = IP2Int(addr)
            self.addRouteToRIB(r)
        self.refreshRIB()

    def sendRegularUpdate(self):
        pkt = RipPacket(RIP_COMMAND_RESPONSE, 2)
        for r in self.RIB:
            if r.metric < RIP_METRIC_MAX:
                pkt.addEntry(r.prefix, r.prefixLen, r.nextHop, r.metric)

        if len(pkt.entry) > 0:
            print('s', pkt, pkt.size)
            self.transport.write(pkt.pack(), (RIP_MULTICAST_ADDR, RIP_UDP_PORT))
        else:
            print('s No valid entry to send update packet.')

        reactor.callLater(self.getUpdateTime(), self.sendRegularUpdate)

    # TODO
    def sendRequest(self, route):
        # construct request packet
        pass

    def requestAllRoutes(self):
        pkt = RipPacket(RIP_COMMAND_REQUEST, 2)
        pkt.addEntry(0, 0, 0, 16, 0, 0) # a special entry to request all routing table from neighbors.
        print('s', pkt)
        self.transport.write(pkt.pack(), (RIP_MULTICAST_ADDR, RIP_UDP_PORT))

    '''
        RIB database functions
    '''
    def showRIB(self):
        for r in self.RIB:
            print(r)

    def verifyRoute(self, route):
        # check netmask
        # check prefix
        # check next hop

        if route.metric < RIP_METRIC_MIN:
            return False

        if not route.family == RIP_ADDRESS_FAMILY:
            return False

        return True

    def addRouteToRIB(self, route):
        if self.verifyRoute(route) == False:
            return

        for r in self.RIB:
            if r == route:
                return

        for i in range(0,len(self.RIB)):
            if self.RIB[i] >= route:
                self.RIB.insert(i, route)
                return
        self.RIB.append(route)

    def deleteRouteFromRIB(self, route):
        if len(self.RIB) == 0:
            warn('Nothing to delete in RIB.')
            return
        for i in range(0,len(self.RIB)):
            if self.RIB[i] == route:
                self.RIB.pop(i)

    def refreshRIB(self):
        for r in self.RIB:
            if r.metric >= RIP_METRIC_INFINITY:
                r.metric = RIP_METRIC_INFINITY

'''
    Show available options and details about this program.
'''
def showHelp():
    print('pyrip.py <configFile>')

'''
    Parse input arguments into dictionary.
'''
def inputParser(argv):
    inputDict = {}

    try:
        opts, args = getopt.getopt(argv,'h',['help'])
    except getopt.GetoptError:
        showHelp()
        sys.exit()

    for opt, arg in opts:
        if opt == '-h':
            showHelp()
            sys.exit()

    if len(args) == 0:
        showHelp()
        sys.exit()

    inputDict['configFileName'] = args[0]
    return inputDict

def main(argv):
    reactor.listenMulticast(RIP_UDP_PORT, RIP(inputParser(argv)), listenMultiple=True)
    reactor.run()

if __name__ == '__main__':
    main(sys.argv[1:])