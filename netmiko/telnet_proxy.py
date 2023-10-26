import sys
import socks
import socket
import telnetlib

__all__ = ["Telnet"]

class TelnetProxy(telnetlib.Telnet):
    def __init__(
        self, host=None, port=0, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, proxy_dict=None
    ):
        self.proxy_dict = proxy_dict
        super().__init__(host=host, port=port, timeout=timeout)

    def open(self, host, port=0, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        """
        Connect to a host.
        The optional second argument is the port number, which
        defaults to the standard telnet port (23).

        Don't try to reopen an already connected instance.

        proxy_dict = {
                'proxy_type': socks.SOCKS5,
                'proxy_addr': hostname,
                'proxy_port': port,
                'proxy_username': username,
                'proxy_password': password
            }
        """
        self.eof = 0
        if not port:
            port = telnetlib.TELNET_PORT
        self.host = host
        self.port = port
        self.timeout = timeout

        sys.audit("telnetlib.Telnet.open", self, host, port)

        self.sock = socks.create_connection((host, port), timeout, **self.proxy_dict)
