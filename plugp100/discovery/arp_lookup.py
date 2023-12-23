import asyncio
import functools
import ipaddress
import logging
from math import floor
from typing import Optional

from scapy.layers.l2 import Ether, ARP
from scapy.sendrecv import srp

from plugp100.common.functional.tri import Try, Failure

logger = logging.getLogger(__name__)


class ArpLookup:
    @staticmethod
    async def lookup(
        mac: str,
        network: str,
        timeout: Optional[int] = None,
        allow_promiscuous: bool = True,
    ) -> Try[Optional[str]]:
        """
        Perform an ARP scan on a network to find the IP address associated with a given MAC address.
        Args:
            mac (str): The target MAC address for which to find the corresponding IP address.
            network (str): The network IP range to scan, e.g., "192.168.1.0/24".
            timeout (int): Timeout to wait for ARP response
        Returns:
            Optional[str]: The IP address corresponding to the provided MAC address if found, or None if not found.
        Note:
            This function disables promiscuous mode, sends an ARP request to the specified network using the provided
            MAC address, and captures responses to identify the IP address associated with the MAC address.
            It constructs ARP packets using the Scapy library.
        Example:
            network = "192.168.1.0/24"
            target_mac = "00:11:22:33:44:55"
            ip_address = LocalDeviceFinder.scan_one(network, target_mac)
            if ip_address:
                print(f"The IP address of {target_mac} is {ip_address}")
            else:
                print(f"No IP address found for {target_mac}")
        """
        try:
            from scapy.all import conf as scapyconf

            scapyconf.sniff_promisc = 1 if allow_promiscuous else 0
            arp_request = Ether(dst=mac) / ARP(pdst=network)
            timeout = ArpLookup._estimate_timeout(network) if timeout is None else timeout
            result, _ = await asyncio.get_event_loop().run_in_executor(
                None,
                functools.partial(srp, arp_request, timeout=timeout, verbose=False),
            )
            for sent, received in result:
                return Try.of(received[ARP].psrc)
            return Try.of(None)
        except Exception as e:
            logger.warning("Failed to scan network %s error: %s", network, str(e))
            return Failure(e)

    @staticmethod
    def _estimate_timeout(network: str) -> int:
        network = ipaddress.IPv4Network(network, strict=False)
        ip_count = network.num_addresses
        return floor((ip_count / 128) * 1)


def run_async(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, lambda: f(*args, **kwargs))

    return inner
