#!/usr/bin/env python
from getpass import getpass
from pprint import pprint
from netmiko import ConnectHandler

PASSWORD = getpass()


def main():
    conn = ConnectHandler(
        host="cisco1.lasthop.io",
        device_type="cisco_ios",
        username="username",
        password=PASSWORD,
    )
    # Setting both `use_textfsm` and `use_genie` to True will try textfsm first
    # if structured data is returned genie will be ignored. If textfsm does not
    # return structured data netmiko will try to parse with genie
    output = conn.send_command("show version", use_textfsm=True, use_genie=True)
    # textfsm structured data returned
    pprint(output)


if __name__ == "__main__":
    main()
