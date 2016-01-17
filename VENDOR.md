Steps for adding a new vendor
=======

Create a new vendor directory underneath netmiko/netmiko:

```
$ cd netmiko/netmiko
$ mkdir arista
```
 
Make the directory a Python package:

```
$ cd arista
$ touch __init__.py
```
  
Create a new module for the vendor:

```
$ vi arista_ssh.py
from netmiko.ssh_connection import SSHConnection

class AristaSSH(SSHConnection):

    pass
```
  
Inherit from the SSHConnection class. Note, the netmiko package will need to be in 
your PYTHONPATH

Update \_\_init__.py to export the new class:

```
$ vi __init__.py
from netmiko.arista.arista_ssh import AristaSSH

__all__ = ['AristaSSH']
```

Update the dispatcher adding the new class:  

```
$ cd netmiko/netmiko
$ vi ssh_dispatcher.py
from netmiko.cisco import CiscoIosSSH
from netmiko.cisco import CiscoAsaSSH
from netmiko.arista import AristaSSH            # Add here

CLASS_MAPPER = {
    'cisco_ios'     : CiscoIosSSH,
    'cisco_asa'     : CiscoAsaSSH,
    'arista_eos'    : AristaSSH,        # Add Here (device_type to class mapping)
}
```

Your class will need to support the following methods:

```
def __init__(self, ip, username, password, secret='', port=22, device_type='', verbose=True):
def establish_connection(self, sleep_time=3, verbose=True):
def disable_paging(self):
def find_prompt(self):
def clear_buffer(self):
def send_command(self, command_string, delay_factor=1, max_loops=30):
def strip_prompt(self, a_string):
def strip_command(self, command_string, output):
def normalize_linefeeds(self, a_string):
def enable(self):
def config_mode(self):
def exit_config_mode(self):
def send_config_set(self, config_commands=None):
def cleanup(self):
def disconnect(self):
```

As much as possible, you should re-use the inherited methods from SSHConnection 
and BaseSSHConnection (i.e. only re-write what you have to).

BaseSSHConnection is intended to be generic (i.e. irrespective of the vendor)
SSHConnection is Cisco-IOS specific (because lots of vendors imitate Cisco IOS).

You should also write unit tests and verify the functionality of your new class.
See netmiko/tests/test_cisco_ios.py and netmiko/tests/test_cisco_ios_enable.py.


  

Note, you will also need to update the 'packages' section of 'setup.py' file if you are adding a 
completely new package.
