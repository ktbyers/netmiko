#!/usr/bin/env python
"""Return output from single show cmd using Netmiko."""
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import sys
import threading

try:
    from Queue import Queue
except ImportError:
    from queue import Queue
from datetime import datetime
from getpass import getpass
from typing import Dict

from netmiko import ConnectHandler
from netmiko.utilities import (
    load_devices,
    display_inventory,
    obtain_all_devices,
    obtain_netmiko_filename,
    write_tmp_file,
    ensure_dir_exists,
    find_netmiko_dir,
    SHOW_RUN_MAPPER,
)


NETMIKO_BASE_DIR = "~/.netmiko"
ERROR_PATTERN = "%%%failed%%%"
__version__ = "0.1.0"


def print_output(device_name: str, output: str) -> None:
    """Print device output to stdout."""
    sys.stdout.write("{0}:\n--------------------\n{1}\n\n".format(device_name, output))


def ssh_conn(
    device_name: str,
    a_device: Dict[str, str],
    cli_command: str,
    output_q: Queue,
) -> None:
    """SSH connection thread entry point."""
    try:
        net_connect = ConnectHandler(**a_device)
        net_connect.enable()
        output = net_connect.send_command_expect(cli_command)
        net_connect.disconnect()
    except Exception:
        output = ERROR_PATTERN
    output_q.put({device_name: output})


def parse_arguments() -> "argparse.Namespace":
    """Parse command-line arguments."""
    description = (
        "Return output from single show cmd using Netmiko (defaults to running-config)"
    )
    parser = argparse.ArgumentParser(description=description)
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
    parser.add_argument(
        "--write-output",
        help="Write output to files instead of displaying on console",
        action="store_true",
    )
    parser.add_argument("--version", help="Display version", action="store_true")
    cli_args = parser.parse_args()
    if not cli_args.list_devices and not cli_args.version:
        if not cli_args.devices:
            parser.error("Devices not specified.")
    return cli_args


def main() -> int:
    """Primary execution thread."""
    start_time = datetime.now()
    cli_args = parse_arguments()

    cli_username = cli_args.username if cli_args.username else None
    cli_password = getpass() if cli_args.password else None
    cli_secret = getpass("Enable secret: ") if cli_args.secret else None

    version = cli_args.version
    if version:
        print("netmiko-show v{}".format(__version__))
        return 0
    list_devices = cli_args.list_devices
    if list_devices:
        try:
            my_devices = load_devices()
        except OSError as e:
            sys.stderr.write("ERROR: Could not load device inventory: {0}\n".format(e))
            return 1
        display_inventory(my_devices)
        return 0

    cli_command = cli_args.cmd
    cmd_arg = False
    if cli_command:
        cmd_arg = True
    device_or_group = cli_args.devices.strip()
    use_cached_files = cli_args.use_cache
    hide_failed = cli_args.hide_failed

    output_q = Queue()
    try:
        my_devices = load_devices()
    except OSError as e:
        sys.stderr.write("ERROR: Could not load device inventory: {0}\n".format(e))
        return 1
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
            sys.stderr.write(
                "Error reading from netmiko devices file."
                " Device or group not found: {0}\n".format(device_or_group)
            )
            return 1

    # Retrieve output from devices
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
                    if cli_args.write_output:
                        with open("{0}.txt".format(device_name), "w") as f:
                            f.write(output)
                    else:
                        print_output(device_name, output)
                else:
                    failed_devices.append(device_name)
    else:
        for device_name in device_group:
            file_name = obtain_netmiko_filename(device_name)
            try:
                with open(file_name) as f:
                    output = f.read()
            except IOError:
                sys.stderr.write(
                    "Some cache files are missing: unable to use --use-cache option.\n"
                )
                return 1
            if ERROR_PATTERN not in output:
                if cli_args.write_output:
                    with open("{0}.txt".format(device_name), "w") as f:
                        f.write(output)
                else:
                    print_output(device_name, output)
            else:
                failed_devices.append(device_name)

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


def main_ep() -> None:
    """Primary execution entry point."""
    sys.exit(main())


if __name__ == "__main__":
    main_ep()
