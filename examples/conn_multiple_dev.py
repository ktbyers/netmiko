#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

password = getpass()

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": password,
}

cisco2 = {
    "device_type": "cisco_ios",
    "host": "cisco2.lasthop.io",
    "username": "pyclass",
    "password": password,
}

nxos1 = {
    "device_type": "cisco_nxos",
    "host": "nxos1.lasthop.io",
    "username": "pyclass",
    "password": password,
}

srx1 = {
    "device_type": "juniper_junos",
    "host": "srx1.lasthop.io",
    "username": "pyclass",
    "password": password,
}

for device in (cisco1, cisco2, nxos1, srx1):
    net_connect = ConnectHandler(**device)
    print(net_connect.find_prompt())
    net_connect.disconnect()
