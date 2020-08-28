from netmiko import ConnectHandler, __version__
import os
import logging
from ipaddress import ip_address
import yaml
import functools
from datetime import datetime
import csv

logging.basicConfig(filename="test.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")

PRINT_DEBUG = False


def generate_csv_timestamp():
    """yyyy-MM-dd HH:mm:ss"""
    now = datetime.now()
    t_stamp = f"{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}"
    return t_stamp


def write_csv(device_name, netmiko_func_names):
    results_file = "netmiko_performance.csv"
    file_exists = os.path.isfile(results_file)
    with open(results_file, "a") as csv_file:
        field_names = ["date", "netmiko_version", "device_name"] + netmiko_func_names
        t_stamp = generate_csv_timestamp()
        version = __version__
        csv_write = csv.DictWriter(csv_file, fieldnames=field_names)

        # Write the header only once
        if file_exists:
            csv_write.writeheader()


def f_exec_time(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        print(f"{str(func)}: Elapsed time: {end_time - start_time}")
        return result

    return wrapper_decorator


def read_devices():
    f_name = "test_devices.yml"
    with open(f_name) as f:
        return yaml.load(f)


@f_exec_time
def connect(device):
    with ConnectHandler(**device) as conn:
        prompt = conn.find_prompt()
        PRINT_DEBUG and print(prompt)


@f_exec_time
def send_command_simple(device):
    with ConnectHandler(**device) as conn:
        output = conn.send_command("show ip int brief")
        PRINT_DEBUG and print(output)


@f_exec_time
def send_config_simple(device):
    with ConnectHandler(**device) as conn:
        output = conn.send_config_set("logging buffered 20000")
        PRINT_DEBUG and print(output)


@f_exec_time
def send_config_large_acl(device):
    with ConnectHandler(**device) as conn:
        # Results will be marginally distorted by generating the ACL here.
        cfg = generate_ios_acl(entries=100)
        output = conn.send_config_set(cfg)
        PRINT_DEBUG and print(output)


def generate_ios_acl(entries=100):
    base_cmd = "ip access-list extended netmiko_test_large_acl"
    acl = [base_cmd]
    for i in range(1, entries + 1):
        cmd = f"permit ip host {ip_address('192.168.0.0') + i} any"
        acl.append(cmd)
    return acl


def main():
    PASSWORD = os.environ["NORNIR_PASSWORD"]

    devices = read_devices()
    print("\n\n")
    for dev_name, dev_dict in devices.items():
        print("-" * 80)
        print(f"Device name: {dev_name}")
        print("-" * 12)

        dev_dict["password"] = PASSWORD

        # Run tests
        operations = [
            "connect",
            "send_command_simple",
            "send_config_simple",
            "send_config_large_acl",
        ]
        for op in operations:
            func = globals()[op]
            func(dev_dict)
        print("-" * 80)
        print()

        write_csv(dev_name, operations)

    print("\n\n")


if __name__ == "__main__":
    main()
