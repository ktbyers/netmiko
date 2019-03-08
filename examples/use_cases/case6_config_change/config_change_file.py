#!/usr/bin/env python
from netmiko import Netmiko
from getpass import getpass

nxos1 = {
    "host": "nxos1.twb-tech.com",
    "username": "pyclass",
    "password": getpass(),
    "device_type": "cisco_nxos",
}

cfg_file = "config_changes.txt"
net_connect = Netmiko(**nxos1)

print()
print(net_connect.find_prompt())
output = net_connect.send_config_from_file(cfg_file)
print(output)
print()

net_connect.save_config()
net_connect.disconnect()
