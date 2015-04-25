# Testing

This document covers the test suite for Netmiko.

## The simple version

cd ./netmiko/tests/etc  
cp test_devices.yml.example test_devices.yml  
cp responses.yml.example responses.yml  

edit test_devices.yml  

Pick the device_types you want to test against. Update the ip, username, password, 
secret (optional).

edit responses.yml  

For the device_types that you are testing against, update the base_prompt, router_prompt, 
enable_prompt, interface_ip to match the device(s) you are testing.



## Preparing to Run Tests

In order to run tests, you should create a copy of the following files:

* ./tests/etc/test_devices.yml.example
* ./tests/etc/responses.yml.example

Remove the `.example` extension and edit each of these files.

test_devices.yml should contain a dictionary with keys of device_type, ip, username, password,
secret (optional), and port (optional). This file should NEVER be synced to GitHub since it 
contains your device credentials and since it is specific to your environment.

You should add into test_devices.yml each device that you want to test Netmiko against.


Next, you will need to edit `./tests/etc/responses.yml`. for each vendor, you will need to modify
each of the keys to match your environment.

* `base_prompt`: the prompt stripped of special characters (such as `>` and `#`)
* `router_prompt`: the prompt expected when in user-exec mode (operational mode on Juniper)
* `enable_prompt`: the prompt expected when in enable mode (configuration mode on Juniper)
* `interface_ip`: an IP address that will be present in the equivalent of `show ip interface brief`
* `version_banner`: a string that will be present in the equivalent of `show version`
* `multiple_line_output`: a string that will be present in a command that requires paging to be 
                          disabled (more details below)
* `file_check_cmd`: (optional) See file_check_cmd and config_file below
* `cmd_response_init`: (optional) See cmd_response_init and cmd_response_final below
* `cmd_response_final`: (optional) See cmd_response_init and cmd_response_final below
* `commit_comment`: (optional) See commit testing section below


cmd_response_init/cmd_response_final

These two responses are used in conjunction with the "config" commands in commands.yml. 
cmd_responses_init is the initial state the network device configuration must be in and is taken
from config[0] (in commands.yml). cmd_responses_final is the final state the network device
configuration must be in and is taken from config[2] (in commands.yml).

Basically, the config needs to be set to an initial state so that we can verify the config
changes properly during testing.



## commands.yml

commands.yml indicates commands that will be executed in various parts of the unit tests. There 
should be a command dictionary corresponding to each support Netmiko device_type. You will need to
make sure that the commands sent in the "config" match the responses in cmd_response_init /
cmd_response_final (see cmd_response_init section above).


## Running Tests

Netmiko uses [`pytest`](http://pytest.org/latest/).  
