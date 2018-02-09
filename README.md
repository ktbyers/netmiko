[![PyPI](https://img.shields.io/pypi/v/netmiko.svg)](https://pypi.python.org/pypi/netmiko)
  
  
Netmiko
=======

Multi-vendor library to simplify Paramiko SSH connections to network devices

Python 2.7, 3.5, 3.6  

#### Requires:

Paramiko >= 2  
scp >= 0.10.0  
pyyaml  
pyserial  
textfsm  

#### Supports:

###### Regularly tested

Arista vEOS  
Cisco ASA  
Cisco IOS  
Cisco IOS-XE  
Cisco IOS-XR  
Cisco NX-OS  
Cisco SG300  
HP Comware7  
HP ProCurve  
Juniper Junos  
Linux  
  
###### Limited testing

Alcatel AOS6/AOS8  
Avaya ERS  
Avaya VSP  
Brocade VDX  
Brocade MLX/NetIron  
Calix B6  
Cisco WLC  
Dell-Force10  
Dell PowerConnect  
Huawei  
Mellanox  
NetApp cDOT  
Palo Alto PAN-OS  
Pluribus  
Ruckus ICX/FastIron  
Ubiquiti EdgeSwitch  
Vyatta VyOS  

###### Experimental

A10  
Accedian  
Aruba  
Ciena SAOS  
Cisco Telepresence  
Check Point GAiA  
Coriant  
Eltex  
Enterasys  
Extreme EXOS  
Extreme Wing  
F5 LTM  
Fortinet  
MRV Communications OptiSwitch  
Nokia/Alcatel SR-OS  
QuantaMesh  

## Tutorials:

##### Standard Tutorial:

https://pynet.twb-tech.com/blog/automation/netmiko.html

##### SSH Proxy:

https://pynet.twb-tech.com/blog/automation/netmiko-proxy.html

##### Documentation (Stable)

http://netmiko.readthedocs.io/en/stable/index.html

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

#### Establish an SSH connection to the device by passing in the device dictionary.

```py
net_connect = ConnectHandler(**cisco_881)
```

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

#### For long-running commands, use `send_command_expect()`

`send_command_expect` waits for the trailing prompt (or for an optional pattern)
```py
net_connect.send_command_expect('write memory')
```

```
Building configuration...
[OK]
```

#### Enter and exit enable mode.

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
print(output)
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

## Questions/Discussion

If you find an issue with Netmiko, then you can open an issue on this projects issue page here: [https://github.com/ktbyers/netmiko/issues](https://github.com/ktbyers/netmiko/issues)

If you have questions or would like to discuss Netmiko, a Netmiko channel exists on [this Slack](https://networktocode.slack.com) team.  To join, visit [this url](http://slack.networktocode.com/) and request access to the Slack team. Once access is granted you can join the [#netmiko](https://networktocode.slack.com/messages/netmiko/) channel.




---    
Kirk Byers  
Python for Network Engineers  
https://pynet.twb-tech.com  
