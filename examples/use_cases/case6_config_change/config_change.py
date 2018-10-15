#!/usr/bin/env python
from netmiko import Netmiko
from getpass import getpass

nxos1 = {
    "host": "nxos1.twb-tech.com",
    "username": "pyclass",
    "password": getpass(),
    "device_type": "cisco_nxos",
}

commands = ["logging history size 500"]

net_connect = Netmiko(**nxos1)

print()
print(net_connect.find_prompt())
output = net_connect.send_config_set(commands)
output += net_connect.send_command("copy run start")
print(output)
print()
