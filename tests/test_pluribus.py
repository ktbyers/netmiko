#!/usr/bin/env python
from __future__ import print_function
from netmiko import ConnectHandler
from getpass import getpass

#ip_addr = raw_input("Enter IP Address: ")
pwd = getpass()
ip_addr = 'sw05.bjm01'

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
