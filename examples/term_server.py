#!/usr/bin/env python
"""
This is a complicated example, but it illustrates both using a terminal server
and bouncing through multiple devices.

It also illustrates using 'redispatch()' to dynamically switch the Netmiko class

The setup here is:

Linux Server --(ssh)--> Small Switch --(telnet)--> Terminal Server --(serial)--> Juniper SRX
"""
import os
from getpass import getpass
from netmiko import ConnectHandler, redispatch

# Hiding these IP addresses
terminal_server_ip = os.environ["TERMINAL_SERVER_IP"]
public_ip = os.environ["PUBLIC_IP"]

s300_pass = getpass("Enter password of s300: ")
term_serv_pass = getpass("Enter the terminal server password: ")
srx2_pass = getpass("Enter SRX2 password: ")

# For internal reasons I have to bounce through this small switch to access
# my terminal server.
device = {
    "device_type": "cisco_s300",
    "host": public_ip,
    "username": "admin",
    "password": s300_pass,
    "session_log": "output.txt",
}

# Initial connection to the S300 switch
net_connect = ConnectHandler(**device)
print(net_connect.find_prompt())

# Update the password as the terminal server uses different credentials
net_connect.password = term_serv_pass
net_connect.secret = term_serv_pass
# Telnet to the terminal server
command = f"telnet {terminal_server_ip}\n"
net_connect.write_channel(command)
# Use the telnet_login() method to handle the login process
net_connect.telnet_login()
print(net_connect.find_prompt())

# Made it to the terminal server (this terminal server is "cisco_ios")
# Use redispatch to re-initialize the right class.
redispatch(net_connect, device_type="cisco_ios")
net_connect.enable()
print(net_connect.find_prompt())

# Now connect to the end-device via the terminal server (Juniper SRX2)
net_connect.write_channel("srx2\n")
# Update the credentials for SRX2 as these are different.
net_connect.username = "pyclass"
net_connect.password = srx2_pass
# Use the telnet_login() method to connect to the SRX
net_connect.telnet_login()
redispatch(net_connect, device_type="juniper_junos")
print(net_connect.find_prompt())

# Now we could do something on the SRX
output = net_connect.send_command("show version")
print(output)

net_connect.disconnect()
