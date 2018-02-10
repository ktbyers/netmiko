#!/usr/bin/env python

from __future__ import print_function

from os import path

from netmiko import ConnectHandler
from netmiko.py23_compat import raw_input


def main():
    hostname = raw_input("Enter remote host to test: ")

    home_dir = (path.expanduser('~'))
    key_file = "{}/.ssh/cisco_rsa".format(home_dir)

    cisco_test = {
        'ip': hostname,
        'username': 'testuser2',
        'device_type': 'cisco_ios', 
        'use_keys': True, 
        'key_file': key_file,
        'verbose': False}

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
