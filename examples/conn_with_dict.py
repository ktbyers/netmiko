#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
    "device_type": "cisco_ios",
}

net_connect = ConnectHandler(**cisco1)
print(net_connect.find_prompt())
net_connect.disconnect()
