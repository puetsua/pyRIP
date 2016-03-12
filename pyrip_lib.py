# marcos
import struct
import socket

RIP_MULTICAST_ADDR      = '224.0.0.9'
RIP_UDP_PORT            = 520

RIP_COMMAND_REQUEST     = 1
RIP_COMMAND_RESPONSE    = 2

RIP_MAX_ROUTE_ENTRY     = 25

RIP_METRIC_INFINITY     = 16

RIP_DEFAULT_UPDATE      = 30
RIP_DEFAULT_TIMEOUT     = 180
RIP_DEFAULT_GARBAGE     = 120

def IP2INT(addr):                                                               
    return struct.unpack("!I", socket.inet_pton(socket.AF_INET, addr))[0]                       

def INT2IP(addr):                                                               
    return socket.inet_ntop(socket.AF_INET, struct.pack("!I", addr)) 

def PREFIXLEN2MASK(mask):
    return (~(0xffffffff >> mask)&0xffffffff)

def MASK2PREFIXLEN(mask):
    prefixlen = 0
    mask = ~mask&0xffffffff
    while mask > 0:
        mask = mask >> 1
        prefixlen += 1
    return 32-prefixlen
