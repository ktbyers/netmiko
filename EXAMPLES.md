<img src="https://github.com/ktbyers/netmiko/blob/improved_examples/images/netmiko_logo_gh.png" width="640">

Netmiko Examples
=======

A set of common Netmiko use-cases.


## Table of contents

- [Supported Platforms](https://ktbyers.github.io/netmiko/#supported-platforms)
- [Installation](https://ktbyers.github.io/netmiko/#installation)
- [Tutorials/Examples/Getting Started](https://ktbyers.github.io/netmiko/#tutorialsexamplesgetting-started)
- [Common Issues/FAQ](https://ktbyers.github.io/netmiko/#common-issuesfaq)
- [API-Documentation](https://ktbyers.github.io/netmiko/#api-documentation)
- [TextFSM Integration](https://ktbyers.github.io/netmiko/#textfsm-integration)
- [Contributing](https://ktbyers.github.io/netmiko/#contributing)
- [Questions/Discussion](https://ktbyers.github.io/netmiko/#questionsdiscussion)


## How to find a "device_type".

```py
from netmiko import ConnectHandler

# Just pick an 'invalid' device_type
cisco1 = {
    "device_type": "invalid",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": "invalid"
}

net_connect = ConnectHandler(**cisco1)
net_connect.disconnect()
```


#### The above code will output all of the available SSH device types.
#### Switch to 'invalid_telnet' to see 'telnet' device types.

```
Traceback (most recent call last):
  File "invalid_device_type.py", line 12, in <module>
    net_connect = ConnectHandler(**cisco1)
  File "./netmiko/ssh_dispatcher.py", line 263, in ConnectHandler
    "currently supported platforms are: {}".format(platforms_str)
ValueError: Unsupported 'device_type' currently supported platforms are: 
a10
accedian
alcatel_aos
alcatel_sros
apresia_aeos
arista_eos
aruba_os
avaya_ers
avaya_vsp
... and a lot more.
```


## A Simple Example.

```py
from netmiko import ConnectHandler
from getpass import getpass

net_connect = ConnectHandler(
    device_type="cisco_ios",
    host="cisco1.lasthop.io",
    username="pyclass",
    password=getpass(),
)

print(net_connect.find_prompt())
net_connect.disconnect()
```


## Connect using a Dictionary.

```py
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

net_connect = ConnectHandler(**cisco1)
print(net_connect.find_prompt())
net_connect.disconnect()
```


## Connect using a Dictionary and a Context Manager.

```py
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

# Will automatically 'disconnect()'
with ConnectHandler(**cisco1) as net_connect:
    print(net_connect.find_prompt())
```


## Enter Enable Mode.

```py
from netmiko import ConnectHandler
from getpass import getpass

password = getpass()
secret = getpass("Enter secret: ")

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": password,
    "secret": secret,
}

net_connect = ConnectHandler(**cisco1)
# Call 'enable()' method to elevate privileges
net_connect.enable()
print(net_connect.find_prompt())
net_connect.disconnect()
```


## Connecting to Multiple Devices.

```py
from netmiko import ConnectHandler
from getpass import getpass

password = getpass()

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": password,
}

cisco2 = {
    "device_type": "cisco_ios",
    "host": "cisco2.lasthop.io",
    "username": "pyclass",
    "password": password,
}

nxos1 = {
    "device_type": "cisco_nxos",
    "host": "nxos1.lasthop.io",
    "username": "pyclass",
    "password": password,
}

srx1 = {
    "device_type": "juniper_junos",
    "host": "srx1.lasthop.io",
    "username": "pyclass",
    "password": password,
}

for device in (cisco1, cisco2, nxos1, srx1):
    net_connect = ConnectHandler(**device)
    print(net_connect.find_prompt())
    net_connect.disconnect()
```


## Executing a Simple 'show' Command.

```py
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = { 
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

# Show command that we execute.
command = "show ip int brief"

with ConnectHandler(**cisco1) as net_connect:
    output = net_connect.send_command(command)

# Automatically cleans-up the output so that only the show output is returned
print()
print(output)
print()
```

#### Output from the above execution:

```
Password: 

Interface                  IP-Address      OK? Method Status                Protocol
FastEthernet0              unassigned      YES unset  down                  down    
FastEthernet1              unassigned      YES unset  down                  down    
FastEthernet2              unassigned      YES unset  down                  down    
FastEthernet3              unassigned      YES unset  down                  down    
FastEthernet4              10.220.88.20    YES NVRAM  up                    up      
Vlan1                      unassigned      YES unset  down                  down    

```

## Netmiko and TextFSM

[Additional Details on Netmiko and TextFSM](https://pynet.twb-tech.com/blog/automation/netmiko-textfsm.html)

```py
from netmiko import ConnectHandler
from getpass import getpass
from pprint import pprint

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

command = "show ip int brief"
with ConnectHandler(**cisco1) as net_connect:
    # Use TextFSM to retrieve structured data
    output = net_connect.send_command(command, use_textfsm=True)

print()
pprint(output)
print()
```


#### Output from the above execution:

```
Password: 

[{'intf': 'FastEthernet0',
  'ipaddr': 'unassigned',
  'proto': 'down',
  'status': 'down'},
 {'intf': 'FastEthernet1',
  'ipaddr': 'unassigned',
  'proto': 'down',
  'status': 'down'},
 {'intf': 'FastEthernet2',
  'ipaddr': 'unassigned',
  'proto': 'down',
  'status': 'down'},
 {'intf': 'FastEthernet3',
  'ipaddr': 'unassigned',
  'proto': 'down',
  'status': 'down'},
 {'intf': 'FastEthernet4',
  'ipaddr': '10.220.88.20',
  'proto': 'up',
  'status': 'up'},
 {'intf': 'Vlan1',
  'ipaddr': 'unassigned',
  'proto': 'down',
  'status': 'down'}]

```


## Handling Commands that Prompt for Additional Information

```py
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

command = "del flash:/test3.txt"
net_connect = ConnectHandler(**cisco1)

# CLI Interaction is as follows:
# cisco1#delete flash:/testb.txt
# Delete filename [testb.txt]? 
# Delete flash:/testb.txt? [confirm]y

# Use 'send_command_timing' which is entirely delay based.
# strip_prompt=False and strip_command=False make the output
# easier to read in this context.
output = net_connect.send_command_timing(
    command_string=command,
    strip_prompt=False,
    strip_command=False
)
if "Delete filename" in output:
    output += net_connect.send_command_timing(
        command_string="\n",
        strip_prompt=False,
        strip_command=False
    )
if "confirm" in output:
    output += net_connect.send_command_timing(
        command_string="y",
        strip_prompt=False,
        strip_command=False
    )
net_connect.disconnect()

print()
print(output)
print()
```

#### Output from the above execution:

```
Password: 

del flash:/test3.txt
Delete filename [test3.txt]? 
Delete flash:/test3.txt? [confirm]y
cisco1#
cisco1#

```


## Handling Commands that Prompt for Additional Information using 'expect_string'.

```py
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

command = "del flash:/test4.txt"
net_connect = ConnectHandler(**cisco1)

# CLI Interaction is as follows:
# cisco1#delete flash:/testb.txt
# Delete filename [testb.txt]? 
# Delete flash:/testb.txt? [confirm]y

# Use 'send_command' and the 'expect_string' argument (note, expect_string uses 
# RegEx patterns). Netmiko will move-on to the next command when the
# 'expect_string' is detected.

# strip_prompt=False and strip_command=False make the output
# easier to read in this context.
output = net_connect.send_command(
    command_string=command,
    expect_string=r"Delete filename",
    strip_prompt=False,
    strip_command=False
)
output += net_connect.send_command(
    command_string="\n",
    expect_string=r"confirm",
    strip_prompt=False,
    strip_command=False
)
output += net_connect.send_command(
    command_string="y",
    expect_string=r"#",
    strip_prompt=False,
    strip_command=False
)
net_connect.disconnect()

print()
print(output)
print()
```

#### Output from the above execution:

```
$ python send_command_prompting_expect.py 
Password: 

del flash:/test4.txt
Delete filename [test4.txt]? 
Delete flash:/test4.txt? [confirm]y
cisco1#

```

## Configuration changes including write mem

```py
#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

device = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

commands = ["logging buffered 100000"]
with ConnectHandler(**device) as net_connect:
    output = net_connect.send_config_set(commands)
    output += net_connect.save_config()

print()
print(output)
print()
```

#### Netmiko will automatically enter and exit config mode.
#### Output from the above execution:

```
$ python config_change.py 
Password: 

configure terminal
Enter configuration commands, one per line.  End with CNTL/Z.
cisco1(config)#logging buffered 100000
cisco1(config)#end
cisco1#write mem
Building configuration...
[OK]
cisco1#

```


## Configuration changes from a file

```py
#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

device1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

# File in same directory as script that contains
#
# $ cat config_changes.txt 
# --------------
# logging buffered 100000
# no logging console

cfg_file = "config_changes.txt"
with ConnectHandler(**device1) as net_connect:
    output = net_connect.send_config_from_file(cfg_file)
    output += net_connect.save_config()

print()
print(output)
print()
```

#### Netmiko will automatically enter and exit config mode.
#### Output from the above execution:

```
$ python config_change_file.py 
Password: 

configure terminal
Enter configuration commands, one per line.  End with CNTL/Z.
cisco1(config)#logging buffered 100000
cisco1(config)#no logging console
cisco1(config)#end
cisco1#write mem
Building configuration...
[OK]
cisco1#

```
