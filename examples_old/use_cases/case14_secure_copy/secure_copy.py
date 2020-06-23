#!/usr/bin/env python
from getpass import getpass
from netmiko import ConnectHandler, file_transfer

password = getpass()

cisco = {
    "device_type": "cisco_ios",
    "host": "cisco1.twb-tech.com",
    "username": "pyclass",
    "password": password,
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
    overwrite_file=True,
)

print(transfer_dict)
