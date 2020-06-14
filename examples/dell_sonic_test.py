#!/usr/bin/env python
from __future__ import print_function, unicode_literals

# Netmiko is the same as ConnectHandler
from netmiko import Netmiko
from getpass import getpass

net_connect = Netmiko(
    host="10.11.180.17",
    username="admin",
    password="force10",
    device_type="dell_sonic",
)

configs = ["interface Vlan 101", "interface Vlan 201"]

print(net_connect.find_prompt())
#output = net_connect._enter_shell()
#output = net_connect.send_command("terminal length 0")
#print("\nVerifying state {}".format(output))
output = net_connect.send_command("show version")
print("\version state {}".format(output))
output = net_connect.send_command("show Vlan")
print("\status state {}".format(output))
output = net_connect.send_config_set(configs)
output = net_connect.send_command("show Vlan")
print("\status state {}".format(output))
output = net_connect._return_cli()
net_connect.disconnect()


