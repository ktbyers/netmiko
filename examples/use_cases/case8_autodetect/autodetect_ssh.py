#!/usr/bin/env python
from netmiko import SSHDetect, Netmiko
from getpass import getpass

device = {
    "device_type": "autodetect",
    "host": "cisco1.twb-tech.com",
    "username": "pyclass",
    "password": getpass(),
}

guesser = SSHDetect(**device)
best_match = guesser.autodetect()
print(best_match)  # Name of the best device_type to use further
print(guesser.potential_matches)  # Dictionary of the whole matching result

device["device_type"] = best_match
connection = Netmiko(**device)

print(connection.find_prompt())
