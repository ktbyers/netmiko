#!/usr/bin/env python
from netmiko import Netmiko
from getpass import getpass
import time

cisco1 = {
    "host": "cisco1.twb-tech.com",
    "username": "pyclass",
    "password": getpass(),
    "device_type": "cisco_ios",
}

net_connect = Netmiko(**cisco1)
print(net_connect.find_prompt())
net_connect.write_channel("show ip int brief\n")
time.sleep(1)
output = net_connect.read_channel()
print(output)
net_connect.disconnect()
