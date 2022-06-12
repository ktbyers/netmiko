#!/usr/bin/env python
"""Create grep like remote behavior on show run or command output."""
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import sys
import os
import subprocess
import threading

try:
    from Queue import Queue
except ImportError:
    from queue import Queue
from datetime import datetime
from getpass import getpass

from netmiko import ConnectHandler
from netmiko.utilities import load_devices, display_inventory
from netmiko.utilities import obtain_all_devices
from netmiko.utilities import obtain_netmiko_filename, write_tmp_file, ensure_dir_exists
from netmiko.utilities import find_netmiko_dir
from netmiko.utilities import SHOW_RUN_MAPPER

GREP = "/bin/grep"
if not os.path.exists(GREP):
    GREP = "/usr/bin/grep"
NETMIKO_BASE_DIR = "~/.netmiko"
ERROR_PATTERN = "%%%failed%%%"
__version__ = "0.1.0"


def grepx(files, pattern, grep_options, use_colors=True):
    """Call system grep"""
    if not isinstance(files, (list, tuple)):
        files = [files]
    if use_colors:
        grep_options += ["--color=auto"]

    # Make grep output look nicer by 'cd netmiko_full_dir'
    _, netmiko_full_dir = find_netmiko_dir()
    os.chdir(netmiko_full_dir)
    # Convert files to strip off the directory
    retrieve_file = lambda x: x.split("/")[-1]  # noqa
    files = [retrieve_file(a_file) for a_file in files]
    files.sort()
    grep_list = [GREP] + grep_options + [pattern] + files
    proc = subprocess.Popen(grep_list, shell=False)
    proc.communicate()
    return ""


def ssh_conn(device_name, a_device, cli_command, output_q):
    try:
        net_connect = ConnectHandler(**a_device)
        net_connect.enable()
        output = net_connect.send_command_expect(cli_command)
        net_connect.disconnect()
    except Exception:
        output = ERROR_PATTERN
    output_q.put({device_name: output})


def parse_arguments(args):
    """Parse command-line arguments."""
    description = "Grep pattern search on Netmiko output (defaults to running-config)"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "pattern", nargs="?", help="Pattern to search for", action="store", type=str
    )
    parser.add_argument(
        "devices",
        nargs="?",
        help="Device or group to connect to",
        action="store",
        type=str,
    )
    parser.add_argument(
        "--cmd",
        help="Remote command to execute",
        action="store",
        default=None,
        type=str,
    )
    parser.add_argument("--username", help="Username", action="store", type=str)
    parser.add_argument("--password", help="Password", action="store_true")
    parser.add_argument("--secret", help="Enable Secret", action="store_true")
    parser.add_argument("--use-cache", help="Use cached files", action="store_true")
    parser.add_argument(
        "--list-devices", help="List devices from inventory", action="store_true"
    )
    parser.add_argument(
        "--display-runtime", help="Display program runtime", action="store_true"
    )
    parser.add_argument(
        "--hide-failed", help="Hide failed devices", action="store_true"
    )
    parser.add_argument("--version", help="Display version", action="store_true")
    cli_args = parser.parse_args(args)
    if not cli_args.list_devices and not cli_args.version:
        if not cli_args.devices or not cli_args.pattern:
            parser.error("Grep pattern or devices not specified.")
    return cli_args


def main_ep():
    sys.exit(main(sys.argv[1:]))


def main(args):
    start_time = datetime.now()
    cli_args = parse_arguments(args)

    cli_username = cli_args.username if cli_args.username else None
    cli_password = getpass() if cli_args.password else None
    cli_secret = getpass("Enable secret: ") if cli_args.secret else None

    version = cli_args.version
    if version:
        print("netmiko-grep v{}".format(__version__))
        return 0
    list_devices = cli_args.list_devices
    if list_devices:
        my_devices = load_devices()
        display_inventory(my_devices)
        return 0

    cli_command = cli_args.cmd
    cmd_arg = False
    if cli_command:
        cmd_arg = True
    device_or_group = cli_args.devices.strip()
    pattern = cli_args.pattern
    use_cached_files = cli_args.use_cache
    hide_failed = cli_args.hide_failed

    output_q = Queue()
    my_devices = load_devices()
    if device_or_group == "all":
        device_group = obtain_all_devices(my_devices)
    else:
        try:
            devicedict_or_group = my_devices[device_or_group]
            device_group = {}
            if isinstance(devicedict_or_group, list):
                for tmp_device_name in devicedict_or_group:
                    device_group[tmp_device_name] = my_devices[tmp_device_name]
            else:
                device_group[device_or_group] = devicedict_or_group
        except KeyError:
            return (
                "Error reading from netmiko devices file."
                " Device or group not found: {0}".format(device_or_group)
            )

    # Retrieve output from devices
    my_files = []
    failed_devices = []
    if not use_cached_files:
        for device_name, a_device in device_group.items():
            if cli_username:
                a_device["username"] = cli_username
            if cli_password:
                a_device["password"] = cli_password
            if cli_secret:
                a_device["secret"] = cli_secret
            if not cmd_arg:
                cli_command = SHOW_RUN_MAPPER.get(a_device["device_type"], "show run")
            my_thread = threading.Thread(
                target=ssh_conn, args=(device_name, a_device, cli_command, output_q)
            )
            my_thread.start()
        # Make sure all threads have finished
        main_thread = threading.current_thread()
        for some_thread in threading.enumerate():
            if some_thread != main_thread:
                some_thread.join()
        # Write files
        while not output_q.empty():
            my_dict = output_q.get()
            netmiko_base_dir, netmiko_full_dir = find_netmiko_dir()
            ensure_dir_exists(netmiko_base_dir)
            ensure_dir_exists(netmiko_full_dir)
            for device_name, output in my_dict.items():
                file_name = write_tmp_file(device_name, output)
                if ERROR_PATTERN not in output:
                    my_files.append(file_name)
                else:
                    failed_devices.append(device_name)
    else:
        for device_name in device_group:
            file_name = obtain_netmiko_filename(device_name)
            try:
                with open(file_name) as f:
                    output = f.read()
            except IOError:
                return "Some cache files are missing: unable to use --use-cache option."
            if ERROR_PATTERN not in output:
                my_files.append(file_name)
            else:
                failed_devices.append(device_name)

    grep_options = []
    grepx(my_files, pattern, grep_options)
    if cli_args.display_runtime:
        print("Total time: {0}".format(datetime.now() - start_time))

    if not hide_failed:
        if failed_devices:
            print("\n")
            print("-" * 20)
            print("Failed devices:")
            failed_devices.sort()
            for device_name in failed_devices:
                print("  {}".format(device_name))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
