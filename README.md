netmiko
=======

Multi-vendor library to simplify Paramiko SSH connections to network devices

##### Under early development -- needs more testing #####

Requires:  
Paramiko >= 1.7.5  
Python 2.6 or Python 2.7  
pytest for unit tests (I used pytest 2.6.4)  

Tested on:  
Cisco 881 running IOS 15.4(2)T1  
Cisco CSR1000V running IOS XE 03.13.01.S  
Cisco ASA running 8.0(4)32  
Cisco Nexus 5K  
Cisco Nexus 7K  
Cisco IOS XR ASR9K  
Cisco IOS XRv
Cisco IOS Catalyst 3750
Arista vEOS running 4.12.3  
HP ProCurve 2510-24
HP 2920 - Procurve Software Version WB.15.16.0005
HP 8206 zl - Procurve Software Version K.15.16.0005
HP 870 LSW - Comware Software Version 5.20.105
Juniper SRX100 running 12.1X44-D35.5  
Juniper EX2200 running 12.3R3.4  
F5 LTM (very limited testing)  
 
   
##### Simple example: #####

```
>>> import netmiko

# Create a dictionary representing the device
>>> cisco_881 = {
...     'device_type': 'cisco_ios',
...     'ip':   '10.10.10.10',
...     'username': 'test',
...     'password': 'password',
...     'secret': 'secret',
...     'verbose': False,
... }

# Dynamically select the class to use based on the device_type
>>> SSHClass = netmiko.ssh_dispatcher(device_type=cisco_881['device_type'])

# Supported device_types can be found at:
# https://github.com/ktbyers/netmiko/blob/master/netmiko/ssh_dispatcher.py

```

```
# Establish an SSH connection to the device pass in the device dictionary.
>>> net_connect = SSHClass(**cisco_881)
                
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
<br>      
---    
Kirk Byers  
https://pynet.twb-tech.com
