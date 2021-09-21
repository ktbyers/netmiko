from typing import Any
from paramiko import SSHClient


class SSHClient_noauth(SSHClient):
    """Set noauth when manually handling SSH authentication."""

    def _auth(self, username: str, *args: Any) -> None:
        transport = self.get_transport()
        assert transport is not None
        transport.auth_none(username)
        return
