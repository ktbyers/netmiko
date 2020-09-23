#!/usr/bin/env python
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
    command_string=command, strip_prompt=False, strip_command=False
)
if "Delete filename" in output:
    output += net_connect.send_command_timing(
        command_string="\n", strip_prompt=False, strip_command=False
    )
if "confirm" in output:
    output += net_connect.send_command_timing(
        command_string="y", strip_prompt=False, strip_command=False
    )
net_connect.disconnect()

print()
print(output)
print()
