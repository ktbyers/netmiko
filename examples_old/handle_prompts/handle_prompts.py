#!/usr/bin/env python
"""Handling commands that prompt for additional information."""
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

"""
Cisco IOS behavior on file delete:

pynet-rtr1# delete flash:/small_file_bim.txt
Delete flash:/test1.txt? [confirm]y
pynet-rtr1
"""

net_connect = Netmiko(**my_device)
filename = "text1234.txt"
cmd = "delete flash:{}".format(filename)

# send_command_timing as the router prompt is not returned
output = net_connect.send_command_timing(cmd, strip_command=False, strip_prompt=False)
if "confirm" in output:
    output += net_connect.send_command_timing(
        "\n", strip_command=False, strip_prompt=False
    )

net_connect.disconnect()
print(output)
