#!/usr/bin/env python
from netmiko import Netmiko
from getpass import getpass

net_connect = Netmiko(
    "cisco1.twb-tech.com",
    username="pyclass",
    password=getpass(),
    device_type="cisco_ios",
)

print(net_connect.find_prompt())
net_connect.disconnect()
