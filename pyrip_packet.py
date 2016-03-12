# pyrip_packet.py

import sys
import struct
import socket

from pyrip_lib import *

class RipRouteEntry(object):
    def __init__(self, address, mask, nexthop, metric):
        assert(type(address) is int)
        assert(type(mask) is int)
        assert(type(nexthop) is int)
        assert(type(metric) is int)
        self.address = address
        self.mask = mask
        self.nexthop = nexthop
        self.metric = metric

    def pack(self):
        return struct.pack('!IIII',self.address,self.mask,self.nexthop,self.metric)

    def __repr__(self):
        return '{:s}/{:d}: {:s} ({:d})'.format(INT2IP(self.address),MASK2PREFIXLEN(self.mask),INT2IP(self.nexthop),self.metric)

class RipPacket(object):
    def __init__(self, cmd, version, family = 2, route_tag = 0):
        self.command = cmd
        self.version = version
        self.family = family
        self.route_tag = route_tag
        self.entry = []
        return

    def add_entry(self, address, mask, nexthop, metric):
        if not (type(address) is int and 
                type(mask) is int and 
                type(nexthop) is int):
            return False

        self.entry.append(RipRouteEntry(address, mask, nexthop, metric))
        return True

    def remove_entry(self, address, mask, nexthop):
        assert(type(address) is int)
        assert(type(mask) is int)
        assert(type(nexthop) is int)

        for ent in self.entry:
            if ent.address == ip_addr:
                self.entry.remove(ent)
                return True
        return False
    def __getitem__(self, key):
        return self.entry[key]

    def pack(self):
        header = struct.pack('!BBHHH',self.command,self.version,0,self.family,0)
        entries = b''
        for ent in self.entry:
            entries = entries + struct.pack('!IIII',ent.address,ent.mask,ent.nexthop,ent.metric)
        packet = header + entries
        return packet

    def __repr__(self):
        if self.command == RIP_COMMAND_REQUEST:
            cmd = 'request'
        elif self.command == RIP_COMMAND_RESPONSE:
            cmd = 'response'

        ret = 'v{:d}, {:s}, {:d} entries'.format(self.version,cmd,len(self.entry))
        return ret