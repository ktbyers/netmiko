#!/usr/bin/env python
from netmiko import Netmiko
from getpass import getpass

cisco1 = {
    "host": "cisco1.twb-tech.com",
    "username": "pyclass",
    "password": getpass(),
    "device_type": "cisco_ios_telnet",
}

net_connect = Netmiko(**cisco1)
print(net_connect.send_command("show ip arp"))
net_connect.disconnect()
