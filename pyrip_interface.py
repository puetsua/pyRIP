# pyrip_interface.py
import sys
import socket
import select
import ipaddress as ipaddr

from pyrip_lib import *

ERR_SOCKET_FAILED       = -1
ERR_NONE                = 0
ERR_SOCKET_EXISTED      = 1
ERR_SOCKET_NOTEXISTED   = 2

class RipInterface(object):
    def __init__(self, address, network):
        self.network = network
        self.address = address
        self.sock = None

        # 'fatal error' when code is negative
        # 'no error' when code is zero
        # 'error but can be handled' when code is positive
        self._error_code = 0

    @property
    def error_code(self):
        return _error_code

    @property
    def message(self):
        err_msg = {
            ERR_SOCKET_FAILED       : 'Failed to create socket.',
            ERR_NONE                : 'None',
            ERR_SOCKET_EXISTED      : 'Socket is already created.',
            ERR_SOCKET_NOTEXISTED   : 'Socket is not available.',
            }
        return err_msg[self._error_code]

    def send_unicast(self, data, address):
        if self._error_code < 0:
            return

    def send_multicast(self, data):
        if self._error_code < 0:
            return
        self.sock.sendto(data,(RIP_MULTICAST_ADDR, RIP_UDP_PORT))
        
    def recv(self):
        data = b''
        r, w, e = select.select([self.sock],[],[],0)
        if r:
            data, address = self.sock.recvfrom(RIP_RECV_BUF_SIZE)
        return data

    def socket_open(self):
        if self._error_code < 0:
            return
        if not self.sock == None:
            self._error_code = ERR_SOCKET_FAILED
            self.message = 'OSError({0}): {1}'.format(e.errno, e.strerror)
            return

        # create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RIP_RECV_BUF_SIZE)
        try:
            self.sock.bind((str(self.address), RIP_UDP_PORT))
        except OSError as e:
            self._error_code = ERR_SOCKET_FAILED
            self.sock = None
            self.socket_close()
        
    def socket_close(self):
        if self._error_code < 0:
            return
        self.sock.close()
        