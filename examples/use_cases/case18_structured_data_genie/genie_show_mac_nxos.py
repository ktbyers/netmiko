#!/usr/bin/env python
from getpass import getpass
from pprint import pprint
from netmiko import ConnectHandler

PASSWORD = getpass()


def main():
    conn = ConnectHandler(
        host="nxos1.lasthop.io",
        device_type="cisco_nxos",
        username="username",
        password=PASSWORD,
    )
    output = conn.send_command("show mac address-table", use_genie=True)
    pprint(output)


if __name__ == "__main__":
    main()
