import os
from os import path
import yaml
import functools
from datetime import datetime
import csv

from netmiko import ConnectHandler, __version__
from test_utils import parse_yaml, f_exec_time

import network_utilities


# import logging
# logging.basicConfig(filename='test.log', level=logging.DEBUG)
# logger = logging.getLogger("netmiko")

PRINT_DEBUG = False

PWD = path.dirname(path.realpath(__file__))


def commands(platform):
    """Parse the commands.yml file to get a commands dictionary."""
    test_platform = platform
    commands_yml = parse_yaml(PWD + "/../etc/commands.yml")
    return commands_yml[test_platform]


def generate_csv_timestamp():
    """yyyy-MM-dd HH:mm:ss"""
    now = datetime.now()
    t_stamp = f"{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}"
    return t_stamp


def write_csv(device_name, netmiko_results):
    results_file = "netmiko_performance.csv"
    file_exists = os.path.isfile(results_file)
    with open(results_file, "a") as csv_file:
        field_names = ["date", "netmiko_version", "device_name"] + list(
            netmiko_results.keys()
        )
        t_stamp = generate_csv_timestamp()
        csv_write = csv.DictWriter(csv_file, fieldnames=field_names)

        # Write the header only once
        if not file_exists:
            csv_write.writeheader()

        entry = {
            "date": t_stamp,
            "netmiko_version": __version__,
            "device_name": device_name,
        }

        for func_name, exec_time in netmiko_results.items():
            entry[func_name] = exec_time
        csv_write.writerow(entry)


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
        platform = device["device_type"]
        cmd = commands(platform)["basic"]
        output = conn.send_command(cmd)
        PRINT_DEBUG and print(output)


@f_exec_time
def send_config_simple(device):
    with ConnectHandler(**device) as conn:
        platform = device["device_type"]
        cmd = commands(platform)["config"][0]
        output = conn.send_config_set(cmd)
        PRINT_DEBUG and print(output)


@f_exec_time
def send_config_large_acl(device):

    # Results will be marginally distorted by generating the ACL here.
    device_type = device["device_type"]
    func_name = f"generate_{device_type}_acl"
    func = getattr(network_utilities, func_name)

    with ConnectHandler(**device) as conn:
        cfg = func(entries=100)
        output = conn.send_config_set(cfg)
        PRINT_DEBUG and print(output)


@f_exec_time
def cleanup(device):

    # Results will be marginally distorted by generating the ACL here.
    platform = device["device_type"]
    if "juniper_junos" in platform:
        remove_acl_cmd = "rollback 0"
    elif "cisco_asa" in platform:
        remove_acl_cmd = "clear configure access-list netmiko_test_large_acl"
    else:
        base_acl_cmd = commands(platform)["config_long_acl"]["base_cmd"]
        remove_acl_cmd = f"no {base_acl_cmd}"
    cleanup_generic(device, remove_acl_cmd)


def cleanup_generic(device, command):
    with ConnectHandler(**device) as conn:
        output = conn.send_config_set(command)
        PRINT_DEBUG and print(output)


def remove_old_data():
    results_file = "netmiko_performance.csv"
    entries = []
    with open(results_file) as f:
        read_csv = csv.DictReader(f)
        for entry in read_csv:
            entry = dict(entry)
            if entry["netmiko_version"] != __version__:
                entries.append(entry)

    with open(results_file, "w", newline="") as csv_file:
        field_names = list(entries[0].keys())
        csv_write = csv.DictWriter(csv_file, fieldnames=field_names)
        csv_write.writeheader()
        csv_write.writerows(entries)


def main():
    remove_old_data()
    PASSWORD = os.environ["NORNIR_PASSWORD"]

    devices = read_devices()
    print("\n\n")
    for dev_name, params in devices.items():
        dev_dict = params["device"]
        # if dev_name != "cisco_xr_azure":
        #    continue
        print("-" * 80)
        print(f"Device name: {dev_name}")
        print("-" * 12)

        dev_dict["password"] = PASSWORD
        if dev_name == "cisco_asa":
            dev_dict["secret"] = PASSWORD

        # Run tests
        operations = [
            "connect",
            "send_command_simple",
            "send_config_simple",
            "send_config_large_acl",
            "cleanup",
        ]
        results = {}
        for op in operations:
            func = globals()[op]
            time_delta, result = func(dev_dict)
            if op != "cleanup":
                results[op] = time_delta
        print("-" * 80)
        print()

        write_csv(dev_name, results)

    print("\n\n")


def test_performance():
    main()


if __name__ == "__main__":
    main()
