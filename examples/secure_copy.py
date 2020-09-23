#!/usr/bin/env python
from getpass import getpass
from netmiko import ConnectHandler, file_transfer

cisco = {
    "device_type": "cisco_ios",
    "host": "cisco1.lasthop.io",
    "username": "pyclass",
    "password": getpass(),
}

source_file = "test1.txt"
dest_file = "test1.txt"
direction = "put"
file_system = "flash:"

ssh_conn = ConnectHandler(**cisco)
transfer_dict = file_transfer(
    ssh_conn,
    source_file=source_file,
    dest_file=dest_file,
    file_system=file_system,
    direction=direction,
    # Force an overwrite of the file if it already exists
    overwrite_file=True,
)

print(transfer_dict)
