#!/usr/bin/env python

"""
This will run an ssh command successfully on an Ericsson IPPOS.
SSH must be enabled on the device

"""

from netmiko.ssh_dispatcher import ConnectHandler


def main():
    """
    This will run an ssh command successfully on an Ericsson IPPOS.
    SSH must be enabled on the device
    """

    ericsson_connect = {
        "device_type": "ericsson_ipos",
        "ip": "1.1.1.1",
        "username": "admin",
        "password": "admin",
    }

    net_connect = ConnectHandler(**ericsson_connect)
    output = net_connect.send_command("show ip int brief")
    print(output)

    output_commit = net_connect.commit()
    print(output_commit)


if __name__ == "__main__":
    main()
