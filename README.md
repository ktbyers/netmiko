netmiko
=======

Multi-vendor library to simplify Paramiko SSH connections to network devices

Python 2.6, 2.7, 3.3, 3.4, 3.5  
  
  
<br>
##### Requires: #####
Paramiko >= 1.13+  
scp >= 0.10.0  
pyyaml  
pytest (for unit tests)   
  
  
<br>  
##### Supports: #####
Cisco IOS  
Cisco IOS-XE  
Cisco ASA  
Cisco NX-OS  
Cisco IOS-XR  
Cisco WLC (limited testing)  
Arista vEOS  
HP ProCurve  
HP Comware (limited testing)  
Juniper Junos  
Brocade VDX (limited testing)  
F5 LTM (experimental)  
Huawei (limited testing)  
A10 (limited testing)  
Avaya ERS (limited testing)  
Avaya VSP (limited testing)  
Dell-Force10 DNOS9 (limited testing)  
OVS (experimental)  
Enterasys (experimental)  
Extreme (experiemental)  
Fortinet (experimental)  
Alcatel-Lucent SR-OS (experimental)  

   
<br>      
##### Netmiko Tutorial: #####
See https://pynet.twb-tech.com/blog/automation/netmiko.html  

##### Netmiko and SSH Proxy #####
https://pynet.twb-tech.com/blog/automation/netmiko-proxy.html  
  
  
<br>      
##### Simple example: #####

```
>>> from netmiko import ConnectHandler

# Create a dictionary representing the device.
>>> cisco_881 = {
...     'device_type': 'cisco_ios',
...     'ip':   '10.10.10.10',
...     'username': 'test',
...     'password': 'password',
...     'port' : 8022,          # optional, defaults to 22
...     'secret': 'secret',     # optional, defaults to ''
...     'verbose': False,       # optional, defaults to True
... }
# Supported device_types can be found at:
# https://github.com/ktbyers/netmiko/blob/master/netmiko/ssh_dispatcher.py
# (see CLASS_MAPPER keys)

```

```
# Establish an SSH connection to the device by passing in the device dictionary.
>>> net_connect = ConnectHandler(**cisco_881)

```

```
# Execute show commands on the channel:
>>> output = net_connect.send_command('show ip int brief')
>>> print output
Interface                  IP-Address      OK? Method Status                Protocol
FastEthernet0              unassigned      YES unset  down                  down    
FastEthernet1              unassigned      YES unset  down                  down    
FastEthernet2              unassigned      YES unset  down                  down    
FastEthernet3              unassigned      YES unset  down                  down    
FastEthernet4              10.10.10.10     YES manual up                    up      
Vlan1                      unassigned      YES unset  down                  down    
```

```
# Enter enable mode
>>> net_connect.enable()
```

```
# Execute configuration change commands (will automatically enter into config mode)
>>> config_commands = [ 'logging buffered 20000', 
                        'logging buffered 20010', 
                        'no logging console' ]
>>> output = net_connect.send_config_set(config_commands)
>>> print output

pynet-rtr1#config term
Enter configuration commands, one per line.  End with CNTL/Z.
pynet-rtr1(config)#logging buffered 20000
pynet-rtr1(config)#logging buffered 20010
pynet-rtr1(config)#no logging console
pynet-rtr1(config)#end
pynet-rtr1#

```

  
<br>      
---    
Kirk Byers  
Python for Network Engineers  
https://pynet.twb-tech.com

 
