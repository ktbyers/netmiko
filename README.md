[![PyPI](https://img.shields.io/pypi/v/netmiko.svg)](https://pypi.python.org/pypi/netmiko)
[![Downloads](https://pepy.tech/badge/netmiko)](https://pepy.tech/project/netmiko)


Netmiko
=======

Multi-vendor library to simplify Paramiko SSH connections to network devices

Python 2.7, 3.5, 3.6  

#### Requires:

- Paramiko >= 2.4.1
- scp >= 0.10.0
- pyyaml
- pyserial
- textfsm

#### Supports:

###### Regularly tested

- Arista vEOS
- Cisco ASA
- Cisco IOS
- Cisco IOS-XE
- Cisco IOS-XR
- Cisco NX-OS
- Cisco SG300
- HP Comware7
- HP ProCurve
- Juniper Junos
- Linux

###### Limited testing

- Alcatel AOS6/AOS8
- Apresia Systems AEOS
- Calix B6
- Cisco AireOS (Wireless LAN Controllers)
- Dell OS9 (Force10)
- Dell OS10
- Dell PowerConnect
- Extreme ERS (Avaya)
- Extreme VSP (Avaya)
- Extreme VDX (Brocade)
- Extreme MLX/NetIron (Brocade/Foundry)
- Huawei
- IP Infusion OcNOS
- Mellanox
- NetApp cDOT
- OneAccess
- Palo Alto PAN-OS
- Pluribus
- Ruckus ICX/FastIron
- Ubiquiti EdgeSwitch
- Vyatta VyOS

###### Experimental

- A10
- Accedian
- Aruba
- Ciena SAOS
- Citrix Netscaler
- Cisco Telepresence
- Check Point GAiA
- Coriant
- Dell OS6
- Dell EMC Isilon
- Eltex
- Enterasys
- Extreme EXOS
- Extreme Wing
- Extreme SLX (Brocade)
- F5 TMSH
- F5 Linux
- Fortinet
- MRV Communications OptiSwitch
- Nokia/Alcatel SR-OS
- QuantaMesh
- Rad ETX

## Tutorials:

##### Standard Tutorial:

https://pynet.twb-tech.com/blog/automation/netmiko.html

##### Secure Copy Tutorial:

https://pynet.twb-tech.com/blog/automation/netmiko-scp.html

##### SSH Proxy:

https://pynet.twb-tech.com/blog/automation/netmiko-proxy.html

##### Common Issues:

https://github.com/ktbyers/netmiko/blob/develop/COMMON_ISSUES.md

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

## TextFSM Integration

Netmiko has been configured to automatically look in `~/ntc-template/templates/index` for the ntc-templates index file. Alternatively, you can explicitly tell Netmiko where to look for the TextFSM template directory by setting the `NET_TEXTFSM` environment variable (note, there must be an index file in this directory):

```
export NET_TEXTFSM=/path/to/ntc-templates/templates/
```

[More info on TextFSM and Netmiko](https://pynet.twb-tech.com/blog/automation/netmiko-textfsm.html).

## Questions/Discussion

If you find an issue with Netmiko, then you can open an issue on this projects issue page here: [https://github.com/ktbyers/netmiko/issues](https://github.com/ktbyers/netmiko/issues)

If you have questions or would like to discuss Netmiko, a #netmiko channel exists in [this Slack](https://pynet.slack.com) workspace.  To join, use [this invitation](https://join.slack.com/t/pynet/shared_invite/enQtNTA2MDI3NjU0MTM0LTQ5MjExNGNlNWIzMmRhOTZmNmZkNDA2Nzk4Y2Q1Y2RkMWNhZGEzM2Y5MjI0NDYxODkzM2M0ODIwYzFkMzVmZGY). Once you have entered the workspace, then you can join the #netmiko channel.




---   
Kirk Byers  
Python for Network Engineers  
https://pynet.twb-tech.com  
