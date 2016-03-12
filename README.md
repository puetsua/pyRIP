# pyRIP
![Python](https://img.shields.io/badge/Python-3.5.1-blue.svg) ![Status](https://img.shields.io/badge/Status-Under Development-ff5533.svg)

[pyRIP](https://github.com/hankofficer/pyRIP) is a personal Routing Information Protocol Implementation on Python. In order to familiar with implementing a routing protocol, I opened this project on GitHub for practive and chose easiest routing protocol to implement.

## GOAL
Implement RFC2453(RIPv2) and compatible with RFC1058(RIPv1)

## TODO
1. Regular update packets
2. Handling incoming packets, only v2
3. Routing Information Base for RIP
4. Compatible with v1
5. A module for handling interfaces
6. Trigger update
7. Split-Horizon and Poison Reverse

## Reference
* **RIPv2** [RFC 2453](http://tools.ietf.org/html/rfc2453)
* **RIPv1** [RFC 1058](http://tools.ietf.org/html/rfc1058)