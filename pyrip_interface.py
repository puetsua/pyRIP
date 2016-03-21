# pyrip_interface.py
import sys
import struct
import socket
import select
import ipaddress as ipaddr

from pyrip_lib import *

ERR_SOCKET_FAILED       = -1
ERR_NONE                = 0
ERR_SOCKET_EXISTED      = 1
ERR_SOCKET_NOTEXISTED   = 2

ACTION_NONE             = 0
ACTION_SEND_UNICAST     = 1
ACTION_SEND_MULTICAST   = 2

class RipInterface(object):
    def __init__(self, address, network):
        self.network = network
        self.address = address
        self.sock = None
        self._send_queue = []
        self._recv_queue = []
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

    def update(self):
        if self._error_code < 0:
            return

        read, write, err = select.select([self.sock],[self.sock],[],0)
        for s in read:
            if s == self.sock:
                data, addr_port = self.sock.recvfrom(RIP_RECV_BUF_SIZE)
                # ignore packets from self
                if addr_port[0] == str(self.address):
                    continue
                self._recv_queue.append((ACTION_NONE, data))
        for s in write:
            if s == self.sock:
                if len(self._send_queue) == 0:
                    continue
                action, data = self._send_queue.pop()
                if action == ACTION_SEND_MULTICAST:
                    self.sock.sendto(data, (RIP_MULTICAST_ADDR, RIP_UDP_PORT))
        return

    def send_unicast(self, data, address):
        if self._error_code < 0:
            return
        self._send_queue.append((ACTION_SEND_UNICAST, data))
        return

    def send_multicast(self, data):
        if self._error_code < 0:
            return
        self._send_queue.append((ACTION_SEND_MULTICAST, data))
        return
        
    def recv(self):
        data = b''
        if len(self._recv_queue) > 0:
            action, data = self._recv_queue.pop()
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

        # join multicast
        mreq = struct.pack('4sl', socket.inet_aton(RIP_MULTICAST_ADDR), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
    def socket_close(self):
        if self._error_code < 0:
            return
        self.sock.close()
        