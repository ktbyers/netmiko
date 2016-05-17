# Testing

This document covers the test suite for Netmiko.

<br />
## The simple version

cd ./netmiko/tests/etc  
cp test_devices.yml.example test_devices.yml  
cp responses.yml.example responses.yml  
cp commands.yml.example commands.yml  

<br />
##### edit test_devices.yml  

Pick the device_types you want to test against; update:
* ip 
* username
* password
* secret (optional)

<br />
##### edit responses.yml  

For the device_types that you are testing against, update the following to match the test 
device(s):  
* the base_prompt
* router_prompt
* enable_prompt
* interface_ip

<br />
##### Execute the test
cd ./netmiko/tests

Note, the test_device is the name of the device from test_devices.yml and responses.yml:  
py.test -v test_netmiko_show.py --test_device cisco881  
py.test -v test_netmiko_config.py --test_device cisco881

<br />
There are three tests available:  
* test_netmiko_show.py  
* test_netmiko_config.py  
* test_netmiko_commit.py      # currently only for Juniper  

<br />
