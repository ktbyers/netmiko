#!/usr/bin/env python
"""
This example is serial (i.e. no concurrency). Connect to one device, after the other,
after the other.
"""
from __future__ import print_function, unicode_literals

# Netmiko is the same as ConnectHandler
from netmiko import Netmiko
from getpass import getpass

password = getpass()

cisco1 = {
    "host": "host1.domain.com",
    "username": "pyclass",
    "password": password,
    "device_type": "cisco_ios",
}

arista1 = {
    "host": "host2.domain.com",
    "username": "pyclass",
    "password": password,
    "device_type": "arista_eos",
}

srx1 = {
    "host": "host3.domain.com",
    "username": "pyclass",
    "password": password,
    "device_type": "juniper_junos",
}

for device in (cisco1, arista1, srx1):
    net_connect = Netmiko(**device)
    print(net_connect.find_prompt())
