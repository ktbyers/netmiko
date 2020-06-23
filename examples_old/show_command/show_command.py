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

output = net_connect.send_command("show ip int brief")
print(output)

net_connect.disconnect()
