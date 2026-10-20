"""Local-network mDNS alias advertisement for the buyer portal."""
import ipaddress
import logging
import os
import socket

from zeroconf import IPVersion, ServiceInfo, Zeroconf

from app.config import MDNS_ADDRESS, MDNS_HOSTNAME

log = logging.getLogger(__name__)


def _advertised_address() -> str:
    """Use an explicit address when supplied; otherwise use the active LAN route."""
    if MDNS_ADDRESS:
        return str(ipaddress.IPv4Address(MDNS_ADDRESS))
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No traffic is sent.  This asks Windows which LAN interface would be
        # used for an external route, avoiding virtual-adapter addresses.
        probe.connect(('8.8.8.8', 80))
        return str(ipaddress.IPv4Address(probe.getsockname()[0]))
    finally:
        probe.close()


class MdnsAlias:
    """Publishes an A record for pfgcravings.local plus HTTP service metadata."""

    def __init__(self):
        self.zeroconf = None
        self.info = None

    def start(self):
        if not MDNS_HOSTNAME:
            return
        address = _advertised_address()
        hostname = f'{MDNS_HOSTNAME}.'
        port = int(os.getenv('PFG_PORT', '80'))
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.info = ServiceInfo(
            '_http._tcp.local.',
            'PFG Cravings._http._tcp.local.',
            addresses=[socket.inet_aton(address)],
            port=port,
            properties={'path': '/', 'hostname': MDNS_HOSTNAME},
            server=hostname,
        )
        self.zeroconf.register_service(self.info, allow_name_change=True)
        log.info('mDNS alias available at http://%s (%s)', MDNS_HOSTNAME, address)

    def stop(self):
        if not self.zeroconf:
            return
        try:
            if self.info:
                self.zeroconf.unregister_service(self.info)
        finally:
            self.zeroconf.close()
            self.info = None
            self.zeroconf = None
