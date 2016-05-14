"""Miscellaneous utility functions."""
import sys
import io
import os


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
    yaml_devices_file = find_file()
    return load_yaml_file(yaml_devices_file)


def find_file(file_name=None):
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
