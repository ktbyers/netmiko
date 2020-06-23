#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass


cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
    "ssh_config_file": "~/.ssh/ssh_config",
}

with ConnectHandler(**cisco1) as net_connect:
    output = net_connect.send_command("show users")

print(f"\n{output}\n")
