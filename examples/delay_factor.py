#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass
from datetime import datetime

cisco1 = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

command = "copy flash:c880data-universalk9-mz.155-3.M8.bin flash:test1.bin"

# Start clock
start_time = datetime.now()

net_connect = ConnectHandler(**cisco1)

# Netmiko normally allows 100 seconds for send_command to complete
# delay_factor=4 would allow 400 seconds.
output = net_connect.send_command_timing(
    command, strip_prompt=False, strip_command=False, delay_factor=4
)
if "Destination filename" in output:
    print("Starting copy...")
    output += net_connect.send_command("\n", delay_factor=4, expect_string=r"#")
net_connect.disconnect()

end_time = datetime.now()
print(f"\n{output}\n")
print("done")
print(f"Execution time: {start_time - end_time}")
