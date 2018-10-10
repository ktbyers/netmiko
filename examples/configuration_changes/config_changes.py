#!/usr/bin/env python
from __future__ import print_function, unicode_literals

# Netmiko is the same as ConnectHandler
from netmiko import Netmiko
from getpass import getpass

my_device = {
    "host": "host.domain.com",
    "username": "pyclass",
    "password": getpass(),
    "device_type": "cisco_ios",
}

net_connect = Netmiko(**my_device)
cfg_commands = ["logging buffered 10000", "no logging console"]

# send_config_set() will automatically enter/exit config mode
output = net_connect.send_config_set(cfg_commands)
print(output)

net_connect.disconnect()
