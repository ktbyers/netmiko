#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

command = "copy flash:c880data-universalk9-mz.155-3.M8.bin flash:test1.bin"

net_connect = ConnectHandler(**cisco1)
net_connect.send_config_set("no file prompt")
print("Starting copy...")

# Netmiko normally allows 100 seconds for send_command to complete
# delay_factor=8 would allow 800 seconds.
output = net_connect.send_command(command, delay_factor=8)
net_connect.disconnect()

print(f"\n{output}\n")
print("done")
