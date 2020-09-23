#!/usr/bin/env python
from netmiko import Netmiko
from getpass import getpass

device = {
    "host": "srx1.twb-tech.com",
    "username": "pyclass",
    "password": getpass(),
    "device_type": "juniper_junos",
}

commands = ["set system syslog archive size 240k files 3 "]

net_connect = Netmiko(**device)

print()
print(net_connect.find_prompt())
output = net_connect.send_config_set(commands, exit_config_mode=False)
output += net_connect.commit(and_quit=True)
print(output)
print()

net_connect.disconnect()
