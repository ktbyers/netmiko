#!/usr/bin/env python
from netmiko import ConnectHandler
from os import path


def main():

    try:
        hostname = raw_input("Enter remote host to test: ")
    except NameError:
        hostname = input("Enter remote host to test: ")

    home_dir = path.expanduser("~")
    key_file = "{}/.ssh/cisco_rsa".format(home_dir)

    cisco_test = {
        "ip": hostname,
        "username": "testuser2",
        "device_type": "cisco_ios",
        "use_keys": True,
        "key_file": key_file,
        "verbose": False,
    }

    net_connect = ConnectHandler(**cisco_test)
    print()
    print("Checking prompt: ")
    print(net_connect.find_prompt())
    print()
    print("Testing show ip int brief: ")
    output = net_connect.send_command("show ip int brief")
    print(output)
    print()


if __name__ == "__main__":
    main()
