#!/usr/bin/env python
'''
Test Netmiko on Cisco TelePresence Video device (C, SX, DX, EX, MX)
'''

from netmiko import ConnectHandler, cisco
    
mydevice = {
'device_type': 'cisco_tp',
'ip': '192.168.105.1',
'username': 'admin',
'password': 'Tandberg',
'verbose':True
}     

ssh_conn = ConnectHandler(**mydevice)
print( "\n\n")


command_list = ['help', 'whoami', 'whoaami', 'echo test', 'xconfig']
#command_list = ['help', 'whoami', 'whoaami', 'echo test']

ssh_conn = ConnectHandler(**mydevice)
print( "\n\n")

for command in command_list:
    print('>>> running command : ' + command)
    output = ssh_conn.send_command(command)
    print('Result = ' + output + '\n')