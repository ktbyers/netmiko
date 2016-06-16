Netmiko
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
Cisco WLC  
Arista vEOS  
HP ProCurve  
Juniper Junos  
Palo Alto PAN-OS  
Linux (limited testing)  
HP Comware (limited testing)  
Brocade VDX (limited testing)  
Huawei (limited testing)  
Avaya ERS (limited testing)  
Avaya VSP (limited testing)  
A10 (experimental)  
F5 LTM (experimental)  
Dell-Force10 DNOS9 (limited testing)  
Enterasys (experimental)  
Extreme (experiemental)  
Fortinet (experimental)  
Alcatel-Lucent SR-OS (experimental)  

   
<br>
## Tutorials:

##### Standard Tutorial: #####
https://pynet.twb-tech.com/blog/automation/netmiko.html
  
##### SSH Proxy: #####
https://pynet.twb-tech.com/blog/automation/netmiko-proxy.html
  
  
<br>
## Examples:

#### Create a dictionary representing the device.

Supported device_types can be found [here](https://github.com/ktbyers/netmiko/blob/master/netmiko/ssh_dispatcher.py), see CLASS_MAPPER keys.
```py
from netmiko import ConnectHandler

cisco_881 = {
    'device_type': 'cisco_ios',
    'ip':   '10.10.10.10',
    'username': 'test',
    'password': 'password',
    'port' : 8022,          # optional, defaults to 22
    'secret': 'secret',     # optional, defaults to ''
    'verbose': False,       # optional, defaults to False
}

```

<br>
#### Establish an SSH connection to the device by passing in the device dictionary.
```py
net_connect = ConnectHandler(**cisco_881)
```

<br>
#### Execute show commands.
```py
output = net_connect.send_command('show ip int brief')
print(output)
```
```
Interface                  IP-Address      OK? Method Status                Protocol
FastEthernet0              unassigned      YES unset  down                  down    
FastEthernet1              unassigned      YES unset  down                  down    
FastEthernet2              unassigned      YES unset  down                  down    
FastEthernet3              unassigned      YES unset  down                  down    
FastEthernet4              10.10.10.10     YES manual up                    up      
Vlan1                      unassigned      YES unset  down                  down    
```

<br>
#### For long-running commands, use `send_command_expect()`
```py
net_connect.send_command('write memory')
```
returns a partial response:
```
Building configuration...
```
`send_command_expect` waits for the command prompt, or optional expect value to return.
```py
net_connect.send_command_expect('write memory')
```
returns the full output from the command:
```
Building configuration...
Compressed configuration from 543610 bytes to 149342 bytes[OK]
```


#### Enter and Exit enable mode
```py
net_connect.enable()
net_connect.exit_enable_mode()
```
#### Execute configuration change commands (will automatically enter into config mode)
```py
config_commands = [ 'logging buffered 20000', 
                    'logging buffered 20010', 
                    'no logging console' ]
output = net_connect.send_config_set(config_commands)
print( output )
```
```
pynet-rtr1#config term
Enter configuration commands, one per line.  End with CNTL/Z.
pynet-rtr1(config)#logging buffered 20000
pynet-rtr1(config)#logging buffered 20010
pynet-rtr1(config)#no logging console
pynet-rtr1(config)#end
pynet-rtr1#
```

---    
Kirk Byers
Python for Network Engineers
(https://pynet.twb-tech.com) 
