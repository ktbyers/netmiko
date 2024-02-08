<img src="https://ktbyers.github.io/netmiko/images/netmiko_logo_gh.png" width="320">

Netmiko Examples
=======

A set of common Netmiko use cases.

<br />

## Table of contents

#### Available Device Types
- [Available device types](#available-device-types-1)

#### Simple Examples
- [Simple example](#simple-example)
- [Connect using a dictionary](#connect-using-a-dictionary)
- [Dictionary with a context manager](#dictionary-with-a-context-manager)
- [Enable mode](#enable-mode)

#### Multiple Devices (simple example)
- [Connecting to multiple devices](#connecting-to-multiple-devices)

#### Show Commands
- [Executing a show command](#executing-show-command)
- [Handling commands that prompt (timing)](#handling-commands-that-prompt-timing)
- [Handling commands that prompt (expect_string)](#handling-commands-that-prompt-expect_string)
- [Using global_delay_factor](#using-global_delay_factor)
- [Adjusting delay_factor](#adjusting-delay_factor)

#### Parsers (TextFSM and Genie)
- [TextFSM example](#using-textfsm)
- [Genie example](#using-genie)

#### Configuration Changes
- [Configuration changes](#configuration-changes-1)
- [Configuration changes from a file](#configuration-changes-from-a-file)

#### SSH keys and SSH config_file
- [SSH keys](#ssh-keys)
- [SSH config file](#ssh-config-file)

#### Logging and Session Log
- [Session log](#session-log)
- [Standard logging](#standard-logging)

#### Secure Copy
- [Secure Copy](#secure-copy-1)

#### Auto Detection of Device Type
- [Auto detection using SSH](#auto-detection-using-ssh)
- [Auto detection using SNMPv3](#auto-detection-using-snmpv3)
- [Auto detection using SNMPv2c](#auto-detection-using-snmpv2c)

#### Terminal Server Example
- [Terminal Server and Redispatch](#terminal-server-and-redispatch)


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

## Using TTP

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

# write template to file
ttp_raw_template = """
interface {{ interface }}
 description {{ description }}
"""

with open("show_run_interfaces.ttp", "w") as writer:
    writer.write(ttp_raw_template)

command = "show run | s interfaces"
with ConnectHandler(**cisco1) as net_connect:
    # Use TTP to retrieve structured data
    output = net_connect.send_command(
        command, use_ttp=True, ttp_template="show_run_interfaces.ttp"
    )

print()
pprint(output)
print()
```


#### Output from the above execution:

```
 [[[{'description': 'Router-id-loopback',
     'interface': 'Loopback0'},
    {'description': 'CPE_Acces_Vlan',
     'interface': 'Vlan778'}]]]
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

<br />

## Secure Copy

[Additional details on Netmiko and Secure Copy](https://pynet.twb-tech.com/blog/automation/netmiko-scp.html)

```py
from getpass import getpass
from netmiko import ConnectHandler, file_transfer

cisco = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

# A secure copy server must be enable on the device ('ip scp server enable')
source_file = "test1.txt"
dest_file = "test1.txt"
direction = "put"
file_system = "flash:"

ssh_conn = ConnectHandler(**cisco)
transfer_dict = file_transfer(
    ssh_conn,
    source_file=source_file,
    dest_file=dest_file,
    file_system=file_system,
    direction=direction,
    # Force an overwrite of the file if it already exists
    overwrite_file=True,
)

print(transfer_dict)
```

<br />

## Auto detection using SSH

```py
from netmiko import SSHDetect, ConnectHandler
from getpass import getpass

device = {
    "device_type": "autodetect",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

guesser = SSHDetect(**device)
best_match = guesser.autodetect()
print(best_match)  # Name of the best device_type to use further
print(guesser.potential_matches)  # Dictionary of the whole matching result
# Update the 'device' dictionary with the device_type
device["device_type"] = best_match

with ConnectHandler(**device) as connection:
    print(connection.find_prompt())
```

<br />

## Auto detection using SNMPv2c

Requires 'pysnmp'.

```py
import sys
from getpass import getpass
from netmiko.snmp_autodetect import SNMPDetect
from netmiko import ConnectHandler

host = "cisco1.lasthop.io"
device = {
    "host": host,
    "username": "pyclass", 
    "password": getpass()
}

snmp_community = getpass("Enter SNMP community: ")
my_snmp = SNMPDetect(
    host, snmp_version="v2c", community=snmp_community
)
device_type = my_snmp.autodetect()
print(device_type)

if device_type is None:
    sys.exit("SNMP failed!")

# Update the device dictionary with the device_type and connect
device["device_type"] = device_type
with ConnectHandler(**device) as net_connect:
    print(net_connect.find_prompt())
```

<br />

## Auto detection using SNMPv3

Requires 'pysnmp'.

```py
import sys
from getpass import getpass
from netmiko.snmp_autodetect import SNMPDetect
from netmiko import ConnectHandler

device = {"host": "cisco1.lasthop.io", "username": "pyclass", "password": getpass()}

snmp_key = getpass("Enter SNMP community: ")
my_snmp = SNMPDetect(
    "cisco1.lasthop.io",
    snmp_version="v3",
    user="pysnmp",
    auth_key=snmp_key,
    encrypt_key=snmp_key,
    auth_proto="sha",
    encrypt_proto="aes128",
)
device_type = my_snmp.autodetect()
print(device_type)

if device_type is None:
    sys.exit("SNMP failed!")

# Update the device_type with information discovered using SNMP
device["device_type"] = device_type
net_connect = ConnectHandler(**device)
print(net_connect.find_prompt())
net_connect.disconnect()
```

<br />

## Terminal server and redispatch

```py
"""
This is a complicated example.

It illustrates both using a terminal server and bouncing through multiple
devices.

It also illustrates using 'redispatch()' to change the Netmiko class.

The setup is:

Linux Server 
  --> Small Switch (SSH)
        --> Terminal Server (telnet)
              --> Juniper SRX (serial)
"""
import os
from getpass import getpass
from netmiko import ConnectHandler, redispatch

# Hiding these IP addresses
terminal_server_ip = os.environ["TERMINAL_SERVER_IP"]
public_ip = os.environ["PUBLIC_IP"]

s300_pass = getpass("Enter password of s300: ")
term_serv_pass = getpass("Enter the terminal server password: ")
srx2_pass = getpass("Enter SRX2 password: ")

# For internal reasons I have to bounce through this small switch to access
# my terminal server.
device = {
    "device_type": "cisco_s300",
    "host": public_ip,
    "username": "admin",
    "password": s300_pass,
    "session_log": "output.txt",
}

# Initial connection to the S300 switch
net_connect = ConnectHandler(**device)
print(net_connect.find_prompt())

# Update the password as the terminal server uses different credentials
net_connect.password = term_serv_pass
net_connect.secret = term_serv_pass
# Telnet to the terminal server
command = f"telnet {terminal_server_ip}\n"
net_connect.write_channel(command)
# Use the telnet_login() method to handle the login process
net_connect.telnet_login()
print(net_connect.find_prompt())

# Made it to the terminal server (this terminal server is "cisco_ios")
# Use redispatch to re-initialize the right class.
redispatch(net_connect, device_type="cisco_ios")
net_connect.enable()
print(net_connect.find_prompt())

# Now connect to the end-device via the terminal server (Juniper SRX2)
net_connect.write_channel("srx2\n")
# Update the credentials for SRX2 as these are different.
net_connect.username = "pyclass"
net_connect.password = srx2_pass
# Use the telnet_login() method to connect to the SRX
net_connect.telnet_login()
redispatch(net_connect, device_type="juniper_junos")
print(net_connect.find_prompt())

# Now we could do something on the SRX
output = net_connect.send_command("show version")
print(output)

net_connect.disconnect()
```

#### Output from execution of this code (slightly cleaned-up).

```
$ python term_server.py 
Enter password of s300: 
Enter the terminal server password: 
Enter SRX2 password: 

sf-dc-sw1#

twb-dc-termsrv>
twb-dc-termsrv#

pyclass@srx2>

Hostname: srx2
Model: srx110h2-va
JUNOS Software Release []

```
