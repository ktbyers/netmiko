# Testing

This document covers the test suite for Netmiko.

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
* `commit_comment`: (optional) See commit section below
