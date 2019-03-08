#!/usr/bin/env python
from netmiko import Netmiko
from getpass import getpass

key_file = "/home/gituser/.ssh/test_rsa"

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.twb-tech.com",
    "username": "testuser",
    "use_keys": True,
    "key_file": key_file,
}

net_connect = Netmiko(**cisco1)
print(net_connect.find_prompt())
output = net_connect.send_command("show ip arp")
print(output)
