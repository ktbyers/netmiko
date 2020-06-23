# SNMPv3
from netmiko.snmp_autodetect import SNMPDetect
from netmiko import Netmiko
from getpass import getpass

device = {"host": "cisco1.twb-tech.com", "username": "pyclass", "password": getpass()}

snmp_key = getpass("Enter SNMP community: ")
my_snmp = SNMPDetect(
    "cisco1.twb-tech.com",
    snmp_version="v3",
    user="pysnmp",
    auth_key=snmp_key,
    encrypt_key=snmp_key,
    auth_proto="sha",
    encrypt_proto="aes128",
)
device_type = my_snmp.autodetect()
print(device_type)

device["device_type"] = device_type
net_connect = Netmiko(**device)
print(net_connect.find_prompt())
