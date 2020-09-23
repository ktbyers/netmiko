#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

# Will automatically 'disconnect()'
with ConnectHandler(**cisco1) as net_connect:
    print(net_connect.find_prompt())
