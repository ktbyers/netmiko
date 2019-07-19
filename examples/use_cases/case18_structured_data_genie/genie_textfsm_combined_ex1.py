#!/usr/bin/env python
from getpass import getpass
from pprint import pprint
from netmiko import ConnectHandler

PASSWORD = getpass()


def main():
    conn = ConnectHandler(
        host="cisco1.lasthop.io",
        # "cisco_xe" device type will cause textfsm to not return structured data
        device_type="cisco_xe",
        username="username",
        password=PASSWORD,
    )
    # Setting both `use_textfsm` and `use_genie` to True will try textfsm first
    # if structured data is returned genie will be ignored. If textfsm does not
    # return structured data netmiko will try to parse with genie
    output = conn.send_command("show version", use_textfsm=True, use_genie=True)
    # genie structured data returned
    pprint(output)


if __name__ == "__main__":
    main()
