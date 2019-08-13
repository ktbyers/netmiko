#!/usr/bin/env python
from getpass import getpass
from pprint import pprint
from netmiko import ConnectHandler

PASSWORD = getpass()


def main():
    conn = ConnectHandler(
        host="cisco1.lasthop.io",
        device_type="cisco_xe",
        username="username",
        password=PASSWORD,
    )
    output = conn.send_command("show ip route", use_genie=True)
    pprint(output)


if __name__ == "__main__":
    main()
