from typing import Dict, Any, Optional
import socket
import telnetlib

try:
    import socks

    SOCKS_SUPPORTED = True
except ModuleNotFoundError:
    SOCKS_SUPPORTED = False


class Telnet(telnetlib.Telnet):
    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 0,
        timeout: float = socket._GLOBAL_DEFAULT_TIMEOUT,  # type: ignore
        proxy_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.proxy_dict = proxy_dict
        super().__init__(host=host, port=port, timeout=timeout)

    def open(
        self,
        host: str,
        port: int = 0,
        timeout: float = socket._GLOBAL_DEFAULT_TIMEOUT,  # type: ignore
    ) -> None:
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

        if SOCKS_SUPPORTED:
            self.sock = socks.create_connection(
                (host, port), timeout, **self.proxy_dict
            )
        else:
            msg = """
In order to use the telnet socks proxy, you must 'pip install pysocks'. Note, pysocks is
unmaintained (so use at your own risk).
"""
            raise ModuleNotFoundError(msg)
