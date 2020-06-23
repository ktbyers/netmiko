#!/usr/bin/env python
from netmiko import ConnectHandler

cisco1 = {
    # Just pick an 'invalid' device_type
    "device_type": "invalid",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": "invalid",
}

net_connect = ConnectHandler(**cisco1)
net_connect.disconnect()
