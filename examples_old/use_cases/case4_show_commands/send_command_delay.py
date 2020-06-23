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
command = "copy flash:c880data-universalk9-mz.154-2.T1.bin flash:test1.bin"

print()
print(net_connect.find_prompt())
output = net_connect.send_command(command, delay_factor=4)
print(output)
print()
