#!/usr/bin/env python
"""
This will run an ssh command successfully on an extreme switch and so SSH must
be enabled on the device
"""
from netmiko import ConnectHandler


def main():
    """
    This will run an ssh command successfully on an extreme switch and so SSH must
    be enabled on the device
    """
    extremehandle = {
        "device_type": "extreme",
        "ip": "10.54.116.175",
        "username": "admin",
        "password": "",
    }
    net_connect = ConnectHandler(**extremehandle)
    output = net_connect.send_command("show config vlan")
    print(output)


if __name__ == "__main__":
    main()
