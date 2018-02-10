#!/usr/bin/env python
from __future__ import print_function

from getpass import getpass

from netmiko import ConnectHandler
from netmiko.py23_compat import raw_input

ip_addr = raw_input("Enter IP Address: ")
pwd = getpass()

pluribus_ssh_device = {
    'device_type': 'pluribus',
    'ip': ip_addr,
    'username': 'pluriusr',
    'password': pwd,
    'port': 22,
}

print('Opening SSH connection with', ip_addr)
net_connect = ConnectHandler(**pluribus_ssh_device)
print('SSH prompt: {}'.format(net_connect.find_prompt()))
print('Sending l2-table-show')
print('-' * 50)
print(net_connect.send_command('l2-table-show'))
print('-' * 50)
print('Sending lldp-show')
print('-' * 50)
print(net_connect.send_command('lldp-show'))
print('-' * 50)
print('Closing connection...')
net_connect.disconnect()
print('Connection closed.')
