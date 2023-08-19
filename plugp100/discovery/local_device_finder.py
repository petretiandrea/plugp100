import ipaddress
import logging
import re
from functools import reduce
from typing import Optional

import netifaces
from scapy.config import conf
from scapy.layers.l2 import Ether, ARP
from scapy.sendrecv import srp

logger = logging.getLogger(__name__)


class LocalDeviceFinder:
    def __init__(self):
        self._subnets = []
        self._local_devices = []

    async def scan_local_devices(self):
        self._subnets = await self.get_subnets()
        self._local_devices = reduce(list.__add__, [self._scan_local_network(subnet) for subnet in self._subnets])

    async def get_ip_from_mac(self, mac: str) -> Optional[str]:
        return next(
            map(
                lambda x: x['ip'],
                filter(lambda x: x['mac'].replace(":", "").lower() == mac.lower(), self._local_devices)
            ),
            None
        )

    async def get_ip_from_mac_one(self, mac: str) -> Optional[str]:
        if not self._subnets:
            self._subnets = await self.get_subnets()
        new_mac = ':'.join(re.findall('..', mac)) if ':' not in mac else mac
        return next(
            filter(
                lambda x: x is not None,
                [self._arp_one(subnet, new_mac) for subnet in self._subnets]
            ), None
        )

    async def get_subnets(self) -> list[str]:
        subnets = []
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    local_ip = addr_info["addr"]
                    netmask = addr_info["mask"]
                    local_ip = ipaddress.IPv4Address(local_ip)
                    netmask = ipaddress.IPv4Address(netmask)
                    subnet_length = sum(bit == '1' for bit in bin(int(netmask))[2:])
                    if subnet_length > 0:
                        subnets.append(ipaddress.ip_network(f"{local_ip.compressed}/{subnet_length}", False).compressed)

        return subnets

    def _scan_local_network(self, network: str) -> list[dict[str, str]]:
        try:
            conf.sniff_promisc = 0
            conf.promisc = 0  # Disable promiscuous mode
            arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
            result = srp(arp_request, timeout=10, verbose=False)[0]

            devices = []
            for sent, received in result:
                devices.append({'ip': received[ARP].psrc, 'mac': received[ARP].hwsrc})

            return devices
        except Exception as e:
            logger.warning(f"Failed to scan network {network}", e)
            return []

    def _arp_one(self, network: str, mac: str) -> Optional[str]:
        try:
            conf.sniff_promisc = 0
            conf.promisc = 0  # Disable promiscuous mode
            arp_request = Ether(dst=mac) / ARP(pdst=network)
            result = srp(arp_request, timeout=1, verbose=False)[0]
            for sent, received in result:
                return received[ARP].psrc
            return None
        except Exception as e:
            logger.warning(f"Failed to scan network {network}", e)
            return None
