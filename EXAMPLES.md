<img src="https://github.com/ktbyers/netmiko/blob/improved_examples/images/netmiko_logo_gh.png" width="320">

Netmiko Examples
=======

A set of common Netmiko use cases.

<br />

## Table of contents

- [Available device types](#available-device-types)
- [Simple example](#simple-example)
- [Connect using a dictionary](#connect-using-a-dictionary)
- [Dictionary with a context manager](#dictionary-with-a-context-manager)
- [Enable mode](#enable-mode)
- [Connecting to multiple devices](#connecting-to-multiple-devices)
- [Executing a show command](#executing-show-command)
- [Adjusting delay_factor](#adjusting-delay_factor)
- [Using global_delay_factor](#using-global_delay_factor)
- [TextFSM example](#using-textfsm)
- [Genie example](#using-genie)
- [Handling commands that prompt (timing)](#handling-commands-that-prompt-timing)
- [Handling commands that prompt (expect_string)](#handling-commands-that-prompt-expect_string)
- [Configuration changes](#configuration-changes)
- [Configuration changes from a file](#configuration-changes-from-a-file)
- [SSH keys](#ssh-keys)
- [SSH config file](#ssh-config-file)
- [Session log](#session-log)


<br />

## Available device types

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

#### The above code will output all of the available SSH device types. Switch to 'invalid_telnet' to see 'telnet' device types.

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

<br />

## Simple example

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

<br />

## Connect using a dictionary

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

<br />

## Dictionary with a context manager

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

<br />

## Enable mode

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

<br />

## Connecting to multiple devices.

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

<br />

## Executing show command.

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

<br />

## Adjusting delay_factor

[Additional details on delay_factor](https://pynet.twb-tech.com/blog/automation/netmiko-what-is-done.html)

```py
from netmiko import ConnectHandler
from getpass import getpass
from datetime import datetime

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

command = "copy flash:c880data-universalk9-mz.155-3.M8.bin flash:test1.bin"

# Start clock
start_time = datetime.now()

net_connect = ConnectHandler(**cisco1)

# Netmiko normally allows 100 seconds for send_command to complete
# delay_factor=4 would allow 400 seconds.
output = net_connect.send_command_timing(
    command, strip_prompt=False, strip_command=False, delay_factor=4
)
# Router prompted in this example:
# -------
# cisco1#copy flash:c880data-universalk9-mz.155-3.M8.bin flash:test1.bin
# Destination filename [test1.bin]? 
# Copy in progress...CCCCCCC
# -------
if "Destination filename" in output:
    print("Starting copy...")
    output += net_connect.send_command("\n", delay_factor=4, expect_string=r"#")
net_connect.disconnect()

end_time = datetime.now()
print(f"\n{output}\n")
print("done")
print(f"Execution time: {start_time - end_time}")
```

<br />

## Using global_delay_factor

[Additional details on global_delay_factor](https://pynet.twb-tech.com/blog/automation/netmiko-what-is-done.html)

```py
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = { 
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
    # Multiple all of the delays by a factor of two
    "global_delay_factor": 2,
}

command = "show ip arp"
net_connect = ConnectHandler(**cisco1)
output = net_connect.send_command(command)
net_connect.disconnect()

print(f"\n{output}\n")
```

<br />

## Using TextFSM

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

<br />

## Using Genie

```py
from getpass import getpass
from pprint import pprint
from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass()
}

with ConnectHandler(**device) as net_connect:
    output = net_connect.send_command("show ip interface brief", use_genie=True)

print()
pprint(output)
print()
```

#### Output from the above execution:

```
$ python send_command_genie.py 
Password: 

{'interface': {'FastEthernet0': {'interface_is_ok': 'YES',
                                 'ip_address': 'unassigned',
                                 'method': 'unset',
                                 'protocol': 'down',
                                 'status': 'down'},
               'FastEthernet1': {'interface_is_ok': 'YES',
                                 'ip_address': 'unassigned',
                                 'method': 'unset',
                                 'protocol': 'down',
                                 'status': 'down'},
               'FastEthernet2': {'interface_is_ok': 'YES',
                                 'ip_address': 'unassigned',
                                 'method': 'unset',
                                 'protocol': 'down',
                                 'status': 'down'},
               'FastEthernet3': {'interface_is_ok': 'YES',
                                 'ip_address': 'unassigned',
                                 'method': 'unset',
                                 'protocol': 'down',
                                 'status': 'down'},
               'FastEthernet4': {'interface_is_ok': 'YES',
                                 'ip_address': '10.220.88.20',
                                 'method': 'NVRAM',
                                 'protocol': 'up',
                                 'status': 'up'},
               'Vlan1': {'interface_is_ok': 'YES',
                         'ip_address': 'unassigned',
                         'method': 'unset',
                         'protocol': 'down',
                         'status': 'down'}}}

```

<br />

## Handling commands that prompt (timing)

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

<br />

## Handling commands that prompt (expect_string)

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

<br />

## Configuration changes

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

<br />

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

<br />

## SSH keys

```py
from netmiko import ConnectHandler
from getpass import getpass

key_file = "~/.ssh/test_rsa"
cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "testuser",
    "use_keys": True,
    "key_file": key_file,
}

with ConnectHandler(**cisco1) as net_connect:
    output = net_connect.send_command("show ip arp")

print(f"\n{output}\n")
```

<br />

## SSH Config File

```py
#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass


cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
    "ssh_config_file": "~/.ssh/ssh_config",
}

with ConnectHandler(**cisco1) as net_connect:
    output = net_connect.send_command("show users")

print(output)
```

#### Contents of 'ssh_config' file

```
host jumphost
  IdentitiesOnly yes
  IdentityFile ~/.ssh/test_rsa
  User gituser
  HostName pynetqa.lasthop.io

host * !jumphost
  User pyclass
  # Force usage of this SSH config file
  ProxyCommand ssh -F ~/.ssh/ssh_config -W %h:%p jumphost
  # Alternate solution using netcat
  #ProxyCommand ssh -F ./ssh_config jumphost nc %h %p
```

#### Script execution

```
# 3.82.44.123 is the IP address of the 'jumphost'
$ python conn_ssh_proxy.py 
Password: 

Line       User       Host(s)              Idle       Location
*  8 vty 0     pyclass    idle                 00:00:00 3.82.44.123

  Interface    User               Mode         Idle     Peer Address

```

<br />

## Session log

```py
#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
    # File name to save the 'session_log' to
    "session_log": "output.txt"
}

# Show command that we execute
command = "show ip int brief"
with ConnectHandler(**cisco1) as net_connect:
    output = net_connect.send_command(command)
```

#### Contents of 'output.txt' after execution

```
$ cat output.txt 

cisco1#
cisco1#terminal length 0
cisco1#terminal width 511
cisco1#
cisco1#show ip int brief
Interface                  IP-Address      OK? Method Status                Protocol
FastEthernet0              unassigned      YES unset  down                  down    
FastEthernet1              unassigned      YES unset  down                  down    
FastEthernet2              unassigned      YES unset  down                  down    
FastEthernet3              unassigned      YES unset  down                  down    
FastEthernet4              10.220.88.20    YES NVRAM  up                    up      
Vlan1                      unassigned      YES unset  down                  down    
cisco1#
cisco1#exit
```

<br />

## Standard Logging

The below will create a file named "test.log". This file will contain a lot of
low-level details.

```py
from netmiko import ConnectHandler
from getpass import getpass

# Logging section ##############
import logging

logging.basicConfig(filename="test.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")
# Logging section ##############

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
