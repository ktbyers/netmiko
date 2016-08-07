#!/usr/bin/env python
from netmiko import ConnectHandler
from getpass import getpass

#ip_addr = raw_input("Enter IP Address: ")
pwd = getpass()
ip_addr = '184.105.247.70'

telnet_device = {
    'device_type': 'cisco_ios_telnet',
    'ip': ip_addr,
    'username': 'pyclass',
    'password': pwd,
    'port': 23,
} 

ssh_device = {
    'device_type': 'cisco_ios_ssh',
    'ip': ip_addr,
    'username': 'pyclass',
    'password': pwd,
    'port': 22,
} 

print "telnet"
net_connect1 = ConnectHandler(**telnet_device)
print "telnet prompt: {}".format(net_connect1.find_prompt())
print "send_command: "
print '-' * 50
print net_connect1.send_command_timing("show arp")
print '-' * 50
print '-' * 50
print net_connect1.send_command("show run")
print '-' * 50
print

print "SSH"
net_connect2 = ConnectHandler(**ssh_device)
print "SSH prompt: {}".format(net_connect2.find_prompt())
print "send_command: "
print '-' * 50
print net_connect2.send_command("show arp")
print '-' * 50
print '-' * 50
print net_connect1.send_command("show run")
print '-' * 50
print

#output = net_connect.send_command_expect("show version")

#print
#print '#' * 50
#print output
#print '#' * 50
#print
