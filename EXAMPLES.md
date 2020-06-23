
Netmiko Examples
=======

A set of common Netmiko use-cases.


## How to find a "device_type" 

```py
#!/usr/bin/env python
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


### This will output all of the available SSH device types.
### Switch to 'invalid_telnet' to see 'telnet' device types.

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


## A Simple Example

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


## Connect using a Dictionary

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


## Connect using a Dictionary and a Context Manager

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


## Enter Enable Mode

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

## Connecting to Multiple Devices

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


## Executing Simple 'show' Commands

```py
```
