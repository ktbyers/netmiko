#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
    "session_log": "output.txt",
}

# Show command that we execute
command = "show ip int brief"
with ConnectHandler(**cisco1) as net_connect:
    output = net_connect.send_command(command)
