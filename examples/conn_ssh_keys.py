#!/usr/bin/env python
from netmiko import ConnectHandler

key_file = "~/.ssh/test_rsa"
cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "testuser",
    "use_keys": True,
    "key_file": key_file,
}

with ConnectHandler(**cisco1) as net_connect:
    output = net_connect.send_command("show ip arp")

print(f"\n{output}\n")
