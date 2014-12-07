netmiko
=======

Multi-vendor library to simplify Paramiko SSH connections to network devices

##### Under early, early development -- needs considerably more testing #####

Requires:  
Paramiko >= 1.7.5  
Python 2.6 or Python 2.7  
pytest for unit tests (I used pytest 2.6.4)  

Tested on:  
Cisco 881 running IOS 15.4(2)T1  
Cisco CSR1000V running IOS XE 03.13.01.S  
Cisco ASA running 8.0(4)32  
Arista vEOS running 4.12.3  
HP ProCurve 2510-24  
   
   
##### Simple example: #####

```
# Specify the type of device. Currently supported device_types are 'cisco_ios',
# 'cisco_asa', and 'arista_eos'
>>> import netmiko
>>> SSHClass = netmiko.ssh_dispatcher(device_type='cisco_ios')
```

```
# Establish SSH connection to device
>>> net_connect = SSHClass(ip = '10.10.10.10', username = 'username', 
                password = 'password', secret = 'secret')
SSH connection established to 10.10.10.10:22
Interactive SSH session established
```

```
# Execute a show command
>>> output = net_connect.send_command('show ip int brief')
>>> print output
Interface                  IP-Address      OK? Method Status                Protocol
FastEthernet0              unassigned      YES unset  down                  down    
FastEthernet1              unassigned      YES unset  down                  down    
FastEthernet2              unassigned      YES unset  down                  down    
FastEthernet3              unassigned      YES unset  down                  down    
FastEthernet4              10.220.88.20    YES manual up                    up      
Vlan1                      unassigned      YES unset  down                  down    
```

```
# Enter enable mode
>>> net_connect.enable()
```

```
# Execute configuration change commands (will automatically enter into config mode)
>>> config_commands = ['logging buffered 20000', 'logging buffered 20010', 
                                        'no logging console']
>>> output = net_connect.send_config_set(config_commands)
>>> print output

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
