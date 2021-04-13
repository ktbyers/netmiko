#!/usr/bin/env python

# Script: test_cros_mtbr.py
# Author: Maloy Ghosh <mghosh@cdot.in>
#
# Purpose:

from netmiko import ConnectHandler


cros = {
    "device_type": "cros_mtbr",
    "host": "10.0.3.3",
    "username": "rootsystem",
    "password": "Root@123",
}


def main():
    nc = ConnectHandler(**cros)

    output = nc.send_command("show interface configuration brief")
    print(output)

    output = nc.send_config_set(
        [
            "interface physical 7/1/3",
            "admin-status up",
            "ipv4 address 1.1.1.1 prefix 24",
        ]
    )
    print(output)

    output = nc.commit()
    print(output)

    output = nc.send_command("show interface configuration brief")
    print(output)


if __name__ == "__main__":
    main()
