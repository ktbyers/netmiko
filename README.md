[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/netmiko.svg)](https://img.shields.io/pypi/pyversions/netmiko)
[![PyPI](https://img.shields.io/pypi/v/netmiko.svg)](https://pypi.python.org/pypi/netmiko)
[![Downloads](https://pepy.tech/badge/netmiko)](https://pepy.tech/project/netmiko)
[![GitHub contributors](https://img.shields.io/github/contributors/ktbyers/netmiko.svg)](https://GitHub.com/ktbyers/netmiko/graphs/contributors/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

<img src="https://ktbyers.github.io/netmiko/images/netmiko_logo_gh.png" width="320">

Netmiko
=======

Multi-vendor library to simplify CLI connections to network devices

<br />

## Why Netmiko?
Network automation to screen-scraping devices is primarily concerned with gathering output from show commands and with making configuration changes.

Netmiko aims to accomplish both of these operations and to do it across a very broad set of platforms. It seeks to do this while abstracting away low-level state control (i.e. eliminate low-level regex pattern matching to the extent practical).

<br />

## Getting Started
- [Getting Started](#getting-started-1)

<br />

## Examples
*You really should look here.*

- [Netmiko Examples](https://github.com/ktbyers/netmiko/blob/develop/EXAMPLES.md)

<br />


## Supported Platforms

[PLATFORMS](PLATFORMS.md)

<br />


## Installation

To install netmiko, simply us pip:

```
$ pip install netmiko
```

<br />

## API-Documentation

[API-Documentation](https://ktbyers.github.io/netmiko/docs/netmiko/index.html)

<br />

## Common Issues/FAQ

Answers to some [common questions](COMMON_ISSUES.md)

<br />

### Tutorials

- [Netmiko Overview](https://pynet.twb-tech.com/blog/automation/netmiko.html)
- [Secure Copy](https://pynet.twb-tech.com/blog/automation/netmiko-scp.html)
- [Netmiko through SSH Proxy](https://pynet.twb-tech.com/blog/automation/netmiko-proxy.html)
- [Netmiko and TextFSM](https://pynet.twb-tech.com/blog/automation/netmiko-textfsm.html)
- [Netmiko and what constitutes done](https://pynet.twb-tech.com/blog/automation/netmiko-what-is-done.html)

<br />

### Getting Started:

#### Create a dictionary representing the device.

Supported device_types can be found in [ssh_dispatcher.py](https://github.com/ktbyers/netmiko/blob/master/netmiko/ssh_dispatcher.py), see CLASS_MAPPER keys.
```py
from netmiko import ConnectHandler

cisco_881 = {
    'device_type': 'cisco_ios',
    'host':   '10.10.10.10',
    'username': 'test',
    'password': 'password',
    'port' : 8022,          # optional, defaults to 22
    'secret': 'secret',     # optional, defaults to ''
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

<br />

## API-Documentation

<a href="https://ktbyers.github.io/netmiko/docs/netmiko/index.html" title="Docs">API Documentation</a>

Below are some of the particularly handy Classes/functions for easy reference:
- [Base Connection Object](https://ktbyers.github.io/netmiko/docs/netmiko/base_connection.html)
- [SSH Autodetect](https://ktbyers.github.io/netmiko/docs/netmiko/index.html#netmiko.SSHDetect)
- [SSH Dispatcher](https://ktbyers.github.io/netmiko/docs/netmiko/index.html#netmiko.ssh_dispatcher)
- [Redispatch](https://ktbyers.github.io/netmiko/docs/netmiko/index.html#netmiko.redispatch)

<br />

## Contributing

Contributors are welcome.

You can contribute to Netmiko in a variety of ways: answering questions on Slack (see below in Questions/Discussions), responding to issues, adding to the common issues, reporting/fixing bugs, or even adding your own device type.

Before contributing a new vendor/platform device type, remember that any code added needs to be supported in some fashion. To add a vendor/platform you can follow the outline [here](VENDOR.md). Once you've worked on your first pass of your driver and have it functional, you'll need to include test data in order for it to be merged into develop, you can see the general flow of how to do that [here](TESTING.md).

For all code contributions, please ensure that you have ran `black` against the code or your code will fail the Travis CI build.

<br />

## Questions/Discussion

If you find an issue with Netmiko, then you can open an issue on this projects issue page here: [https://github.com/ktbyers/netmiko/issues](https://github.com/ktbyers/netmiko/issues). Please make sure you've read through the common issues and examples prior to opening an issue. Please only open issues for bugs, feature requests, or other topics related to development of Netmiko. If you simply have a question, join us on Slack...

If you have questions or would like to discuss Netmiko, a #netmiko channel exists in [this Slack](https://pynet.slack.com) workspace. To join, use [this invitation](https://join.slack.com/t/pynet/shared_invite/zt-km2k3upf-AkWHY4YEx3sI1R5irMmc7Q). Once you have entered the workspace, then you can join the #netmiko channel.


---
Kirk Byers  
Python for Network Engineers  
https://pynet.twb-tech.com  
