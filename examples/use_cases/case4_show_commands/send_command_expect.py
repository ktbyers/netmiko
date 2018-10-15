#!/usr/bin/env python
from netmiko import Netmiko
from getpass import getpass

cisco1 = {
    "host": "cisco1.twb-tech.com",
    "username": "pyclass",
    "password": getpass(),
    "device_type": "cisco_ios",
}

net_connect = Netmiko(**cisco1)
command = "show ip int brief"

print()
print(net_connect.find_prompt())
output = net_connect.send_command(command, expect_string=r"#")
net_connect.disconnect()
print(output)
print()
