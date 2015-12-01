#!/usr/bin/env python
# This will run an ssh command successfully on an extreme switch and so SSH must be enabled on the device(s).

import sys
sys.path.append('../')
from netmiko import ConnectHandler

extremehandle = {'device_type':'extreme', 'ip' : '10.54.149.80', 'username':'admin', 'password':'',
		 'global_delay_factor': 1}
net_connect = ConnectHandler(**extremehandle)
output = net_connect.send_command('show config vlan')
print(output)
