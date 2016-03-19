# pyrip_packet.py

import sys
import struct
import socket
import ipaddress as ipaddr

from pyrip_lib import *

class RipRouteEntry(object):
    def __init__(self, address, mask, nexthop, metric, family = 2, route_tag = 0):
        assert(type(family) is int)
        assert(type(route_tag) is int)
        assert(type(address) is int)
        assert(type(mask) is int)
        assert(type(nexthop) is int)
        assert(type(metric) is int)
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

class RipPacket(object):
    def __init__(self, cmd = RIP_COMMAND_RESPONSE, version = 2):
        self.command = cmd
        self.version = version

        self.entry = []
        return

    def add_entry(self, network=None, address=None, mask=None, nexthop=None, metric=0, family=2, route_tag=0):
        if not network is None:
            address = int(network.network_address)
            mask = int(network.netmask)

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
        header = struct.pack(RIP_HEADER_PACK_FORMAT,self.command,self.version,0)
        entries = b''
        for ent in self.entry:
            entries = entries + ent.pack()
        packet = header + entries
        return packet

    def unpack(self,data):
        hdr = data[:RIP_HEADER_SIZE]
        data = data[RIP_HEADER_SIZE:]
        self.command, self.version, zero = struct.pack(RIP_HEADER_PACK_FORMAT,data)
        return

    def __repr__(self):
        if self.command == RIP_COMMAND_REQUEST:
            cmd = 'request'
        elif self.command == RIP_COMMAND_RESPONSE:
            cmd = 'response'

        ret = 'v{:d}, {:s}, {:d} entries'.format(self.version,cmd,len(self.entry))
        return ret