#!/usr/bin/env python
# This will run an ssh command successfully on an enterasys SSA and so SSH must be enabled on the device(s).

import sys
sys.path.append('../')
from netmiko import ConnectHandler

enterasyshandle = {'device_type':'enterasys', 'ip' : '10.54.116.175', 'username':'admin', 'password':''}
net_connect = ConnectHandler(**enterasyshandle)
output = net_connect.send_command('show config policy')
print(output)
