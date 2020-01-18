"""ProSafe OS support"""
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class NetgearProSafeSSH(CiscoSSHConnection):
    """ProSafe OS support"""

    def __init__(self, **kwargs):
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        return super().__init__(**kwargs)
