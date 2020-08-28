from netmiko import ConnectHandler
from netmiko.utilities import f_exec_time
import os
import logging
import sys
from ipaddress import ip_address

logging.basicConfig(filename="test.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")

def read_devices():
    f_name = "test_devices.yml"
    with open(f_name) as f:
        return yaml.load(f)


@f_exec_time
def send_command_simple(device):
    with ConnectHandler(**device) as conn:
        output = conn.send_command("show ip int brief")
        print(output)


@f_exec_time
def send_config_simple(device):
    with ConnectHandler(**device) as conn:
        output = conn.send_config_set("logging buffered 20000")
        print(output)


@f_exec_time
def send_config_large_acl(device):
    with ConnectHandler(**device) as conn:
        cfg = generate_ios_acl(entries=100)
        output = conn.send_config_set(cfg)
        print(output)


def generate_ios_acl(entries=100):
    base_cmd = "ip access-list extended netmiko_test_large_acl"
    acl = [base_cmd]
    for i in range(1, entries + 1):
        cmd = f"permit ip host {ip_address('192.168.0.0') + i} any"
        acl.append(cmd)
    return acl


def main():
    PASSWORD = os.environ["NORNIR_PASSWORD"]


    my_device = {
        # "host": "cisco5.lasthop.io",
        "host": "cisco3.lasthop.io",
        "device_type": "cisco_ios",
        "username": "pyclass",
        "password": PASSWORD,
        "conn_timeout": 20,
        # "fast_cli": True,
    }

    operations = ["connect", "send_command_simple", "send_config_simple", "send_config_large_acl"]
    for op in operations:
        func = globals()[op]
        func(my_device)


if __name__ == "__main__":
    main()
