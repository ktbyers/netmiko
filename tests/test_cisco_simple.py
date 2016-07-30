#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

ip_addr = raw_input("Enter IP Address: ")

device = {
    'device_type': 'cisco_ios_telnet',
    'ip': ip_addr,
    'username': 'pyclass',
    'password': getpass(),
    'port': 23,
} 

net_connect = ConnectHandler(**device)
#output = net_connect.send_command_expect("show version")

#print
#print '#' * 50
#print output
#print '#' * 50
#print
