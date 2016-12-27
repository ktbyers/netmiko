#!/usr/bin/env python
'''
Test Netmiko on Windows SSH (install FreeSSHd on windows remote machine as SSH server)
'''

from netmiko import ConnectHandler, windows
    
mydevice = {
'device_type': 'windows',
'ip': '127.0.0.1',
'username': 'cisco',
'password': 'cisco',
'verbose':True
}     

command_list = ['hostname', 'cd..', 'dir *.*']

ssh_conn = ConnectHandler(**mydevice)
print( "\n\n")

for command in command_list:
    print('>>> running command : ' + command)
    output = ssh_conn.send_command(command)
    print('Result = ' + output + '\n')