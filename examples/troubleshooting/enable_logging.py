#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import logging
from netmiko import Netmiko
from getpass import getpass

# This will create a file named 'test.log' in your current directory.
# It will log all reads and writes on the SSH channel.
logging.basicConfig(filename="test.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")

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
