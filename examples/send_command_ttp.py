#!/usr/bin/env python
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

command = "show run"
with ConnectHandler(**cisco1) as net_connect:
    # Use TTP to retrieve structured data
    output = net_connect.send_command(
        command, use_ttp=True, ttp_template="show_run_interfaces.ttp"
    )

print()
pprint(output)
print()
