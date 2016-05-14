"""Miscellaneous utility functions."""
from __future__ import print_function
from __future__ import unicode_literals

import sys
import io
import os

# Dictionary mapping 'show run' for vendors with different command
SHOW_RUN_MAPPER = {
    'juniper': 'show configuration',
    'juniper_junos': 'show configuration',
}


def load_yaml_file(yaml_file):
    """Read YAML file."""
    try:
        import yaml
    except ImportError:
        sys.exit("Unable to import yaml module.")
    try:
        with io.open(yaml_file, encoding='utf-8') as fname:
            return yaml.load(fname)
    except IOError:
        sys.exit("Unable to open YAML file: {0}".format(yaml_file))


def load_devices():
    """Find and load .netmiko.cfg YAML file."""
    yaml_devices_file = find_cfg_file()
    return load_yaml_file(yaml_devices_file)


def find_cfg_file(file_name=None):
    """Look for .netmiko.cfg in current dir, then ~/.netmiko.cfg."""
    check_files = [
        '.netmiko.cfg',
        os.path.expanduser('~') + '/.netmiko.cfg',
    ]
    if file_name:
        check_files.insert(0, file_name)
    for test_file in check_files:
        if os.path.isfile(test_file):
            return test_file
    raise IOError("{} file not found in current dir or home dir.".format(file_name))


def display_inventory(my_devices):
    """Print out inventory devices and groups."""
    inventory_groups = ['all']
    inventory_devices = []
    for k, v in my_devices.items():
        if isinstance(v, list):
            inventory_groups.append(k)
        elif isinstance(v, dict):
            inventory_devices.append((k, v['device_type']))

    inventory_groups.sort()
    inventory_devices.sort(key=lambda x: x[0])
    print("\nDevices:")
    print('-' * 40)
    for a_device, device_type in inventory_devices:
        device_type = "  ({})".format(device_type)
        print("{:<25}{:>15}".format(a_device, device_type))
    print("\n\nGroups:")
    print('-' * 40)
    for a_group in inventory_groups:
        print(a_group)
    print()


def obtain_all_devices(my_devices):
    """Dynamically create 'all' group."""
    new_devices = {}
    for device_name, device_or_group in my_devices.items():
        # Skip any groups
        if not isinstance(device_or_group, list):
            new_devices[device_name] = device_or_group
    return new_devices
