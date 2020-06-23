
Netmiko
=======

A set of very common Netmiko use-cases.

## How to find if a given "device_type" is available

```py
#!/usr/bin/env python
from netmiko import ConnectHandler

cisco1 = {
    # Just pick an 'invalid' device_type
    "device_type": "invalid",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": "invalid"
}

net_connect = ConnectHandler(**cisco1)
net_connect.disconnect()
```

This will output all of the available SSH device types.

```
Traceback (most recent call last):
  File "invalid_device_type.py", line 12, in <module>
    net_connect = ConnectHandler(**cisco1)
  File "/home/kbyers/VENV/nornir_netmiko/lib64/python3.6/site-packages/netmiko/ssh_dispatcher.py", line 263, in ConnectHandler
    "currently supported platforms are: {}".format(platforms_str)
ValueError: Unsupported device_type: currently supported platforms are: 
a10
accedian
alcatel_aos
alcatel_sros
apresia_aeos
arista_eos
aruba_os
avaya_ers
avaya_vsp
... and a lot more
```


## The Simplest Example

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
```
