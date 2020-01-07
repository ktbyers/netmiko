![PyPI - Python Version](https://img.shields.io/pypi/pyversions/netmiko.svg)
[![PyPI](https://img.shields.io/pypi/v/netmiko.svg)](https://pypi.python.org/pypi/netmiko)
[![Downloads](https://pepy.tech/badge/netmiko)](https://pepy.tech/project/netmiko)
![GitHub contributors](https://img.shields.io/github/contributors/ktbyers/netmiko.svg)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


Netmiko
=======

Multi-vendor library to simplify Paramiko SSH connections to network devices

## Quick Links

- [Supported Platforms](https://ktbyers.github.io/netmiko/#supported-platforms)
- [Installation](https://ktbyers.github.io/netmiko/#installation)
- [Tutorials/Examples/Getting Started](https://ktbyers.github.io/netmiko/#tutorialsexamplesgetting-started)
- [Common Issues/FAQ](https://ktbyers.github.io/netmiko/#common-issuesfaq)
- [API-Documentation](https://ktbyers.github.io/netmiko/#api-documentation)
- [TextFSM Integration](https://ktbyers.github.io/netmiko/#textfsm-integration)
- [Contributing](https://ktbyers.github.io/netmiko/#contributing)
- [Questions/Discussion](https://ktbyers.github.io/netmiko/#questionsdiscussion)


## Supported Platforms

Netmiko supports a wide range of devices. These devices fall into three categories:
- Regularly Tested
- Limited Testing
- Experimental

Regularly tested means we try to run our full test suite against that set of devices prior to each Netmiko release.

Limited testing means the config and show operation system tests passed against a test on that platform at one point in time so we are reasonably comfortable the driver should generally work.

Experimental means that we reviewed the PR and the driver seems reasonable, but we don't have good data on whether the driver fully passes the unit tests or how reliably it works.

Click [PLATFORMS](PLATFORMS.md) for a list of all supported platforms.


## Installation

To install netmiko, simply us pip:

```
$ pip install netmiko
```

Netmiko has the following requirements (which pip will install for you)
- Paramiko >= 2.4.3
- scp >= 0.13.2
- pyserial
- textfsm


## Tutorials/Examples/Getting Started

### Tutorials:

- [Getting Started](https://pynet.twb-tech.com/blog/automation/netmiko.html)
- [Secure Copy](https://pynet.twb-tech.com/blog/automation/netmiko-scp.html)
- [Netmiko through SSH Proxy](https://pynet.twb-tech.com/blog/automation/netmiko-proxy.html)
- [Netmiko and TextFSM](https://pynet.twb-tech.com/blog/automation/netmiko-textfsm.html)
- [Netmiko and what constitutes done](https://pynet.twb-tech.com/blog/automation/netmiko-what-is-done.html)


### Example Scripts:

See the following directory for [example scripts](https://github.com/ktbyers/netmiko/tree/develop/examples/use_cases), including examples of:

- [Simple Connection](https://github.com/ktbyers/netmiko/blob/develop/examples/use_cases/case1_simple_conn/simple_conn.py)
- [Sending Show Commands](https://github.com/ktbyers/netmiko/tree/develop/examples/use_cases/case4_show_commands)
- [Sending Configuration Commands](https://github.com/ktbyers/netmiko/tree/develop/examples/use_cases/case6_config_change)
- [Handling Additional Prompting](https://github.com/ktbyers/netmiko/blob/develop/examples/use_cases/case5_prompting/send_command_prompting.py)
- [Connecting with SSH Keys](https://github.com/ktbyers/netmiko/blob/develop/examples/use_cases/case9_ssh_keys/conn_ssh_keys.py)
- [Cisco Genie Integration](https://github.com/ktbyers/netmiko/blob/develop/examples/use_cases/case18_structured_data_genie)


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


## Common Issues/FAQ

Answers to some [common questions](COMMON_ISSUES.md)

Topics covered in above document:
- Handling commands that prompt for additional input
- Enabling logging of all reads/writes of the communication channel
- Redispatch -- or connecting through a terminal server


## API-Documentation

<a href="https://ktbyers.github.io/netmiko/docs/netmiko/index.html" title="Docs">API Documentation</a>

Below are some of the particularly handy Classes/functions for easy reference:
- [Base Connection Object](https://ktbyers.github.io/netmiko/docs/netmiko/base_connection.html)
- [SSH Autodetect](https://ktbyers.github.io/netmiko/docs/netmiko/index.html#netmiko.SSHDetect)
- [SSH Dispatcher](https://ktbyers.github.io/netmiko/docs/netmiko/index.html#netmiko.ssh_dispatcher)
- [Redispatch](https://ktbyers.github.io/netmiko/docs/netmiko/index.html#netmiko.redispatch)


## TextFSM Integration

Netmiko has been configured to automatically look in `~/ntc-template/templates/index` for the ntc-templates index file. Alternatively, you can explicitly tell Netmiko where to look for the TextFSM template directory by setting the `NET_TEXTFSM` environment variable (note, there must be an index file in this directory):

```
export NET_TEXTFSM=/path/to/ntc-templates/templates/
```

[More info on TextFSM and Netmiko](https://pynet.twb-tech.com/blog/automation/netmiko-textfsm.html).


## Contributing

Contributors are always welcome! You can contribute to Netmiko in a variety of ways: spreading the word about Netmiko, answering questions on Slack (see below in Quests/Discussions), responding to issues, adding to the common issues, reporting/fixing bugs, or even adding your own device type.

Before contributing a new vendor/platform device type, remember that any code added needs to be supported in some fashion (much more so for the "regularly tested" devices and the core of Netmiko)! To add a vendor/platform you can follow the outline [here](VENDOR.md). Once you've worked on your first pass of your driver and have it functional, you'll need to include test data in order for it to be merged into develop, you can see the general flow of how to do that [here](TESTING.md).

For all code contributions, please ensure that you have ran `black` against the code or your code will fail the Travis CI build.


## Questions/Discussion

If you find an issue with Netmiko, then you can open an issue on this projects issue page here: [https://github.com/ktbyers/netmiko/issues](https://github.com/ktbyers/netmiko/issues). Please make sure you've read through the common issues and examples prior to opening an issue. Please only open issues for bugs, feature requests, or other topics related to development of Netmiko. If you simply have a question, join us on Slack...

If you have questions or would like to discuss Netmiko, a #netmiko channel exists in [this Slack](https://pynet.slack.com) workspace. To join, use [this invitation](https://join.slack.com/t/pynet/shared_invite/enQtNTA2MDI3NjU0MTM0LTIyZDdhMTBlOWNmNDJhNjkxZTEyMDg3NTRkOWIxMTUwOTAzYmQ0ZjMwMGMyNTM4N2E1YzA3YWQ1MWFiOWM1YzU). Once you have entered the workspace, then you can join the #netmiko channel.


---
Kirk Byers  
Python for Network Engineers  
https://pynet.twb-tech.com  
