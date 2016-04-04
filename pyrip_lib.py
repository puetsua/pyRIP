import socket, struct

# useful marcos
RIP_MULTICAST_ADDR      = '224.0.0.9'
RIP_UDP_PORT            = 520

RIP_COMMAND_REQUEST     = 1
RIP_COMMAND_RESPONSE    = 2

RIP_METRIC_INFINITY     = 16

RIP_DEFAULT_JITTER_SCALE    = 0.2
RIP_DEFAULT_UPDATE          = 30
RIP_DEFAULT_TIMEOUT         = 180
RIP_DEFAULT_GARBAGE         = 120

RIP_HEADER_SIZE         = 4
RIP_HEADER_PACK_FORMAT  = '!BBH'
RIP_ENTRY_SIZE          = 20
RIP_ENTRY_PACK_FORMAT   = '!HHIIII'

RIP_MAX_ROUTE_ENTRY     = 25
RIP_RECV_BUF_SIZE       = 41600

# it's very unlikely to change in future
RIP_ADDRESS_FAMILY      = 2 

def MaskInt2PrefixLen(maskInt): 
    return bin(maskInt).count('1')

def PrefixLen2MaskInt(prefixLen):
    return 0xffffffff ^ (0xffffffff >> prefixLen)

def Int2IP(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

def IP2Int(ip):
    return struct.unpack("!I", socket.inet_aton(ip))[0]
