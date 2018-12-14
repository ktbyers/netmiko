#!/usr/bin/env python
from __future__ import print_function, unicode_literals

# Netmiko is the same as ConnectHandler
from netmiko import Netmiko
from getpass import getpass

net_connect = Netmiko(
    host="host.domain.com",
    username="pyclass",
    password=getpass(),
    device_type="cisco_ios",
)

print(net_connect.find_prompt())
net_connect.disconnect()
