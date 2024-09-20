#!/usr/bin/env python3
"""Return output from single show cmd using Netmiko."""
import argparse
import sys
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from datetime import datetime
from getpass import getpass

from netmiko.utilities import load_devices, display_inventory
from netmiko.utilities import obtain_netmiko_filename, write_tmp_file, ensure_dir_exists
from netmiko.utilities import find_netmiko_dir
from netmiko.utilities import SHOW_RUN_MAPPER
from netmiko.cli_tools import ERROR_PATTERN, GREP, MAX_WORKERS, __version__
from netmiko.cli_tools.cli_helpers import obtain_devices, update_device_params, ssh_conn


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


def parse_arguments(args):
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
    parser.add_argument("--version", help="Display version", action="store_true")
    cli_args = parser.parse_args(args)
    if not cli_args.list_devices and not cli_args.version:
        if not cli_args.devices:
            parser.error("Devices not specified.")
    return cli_args


def main_ep():
    sys.exit(main(sys.argv[1:]))


def main(args):
    start_time = datetime.now()

    # CLI ARGS #####
    cli_args = parse_arguments(args)

    cli_username = cli_args.username if cli_args.username else None
    cli_password = getpass() if cli_args.password else None
    cli_secret = getpass("Enable secret: ") if cli_args.secret else None

    version = cli_args.version
    if version:
        print("netmiko-show v{}".format(__version__))
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
    pattern = r"."
    use_cached_files = cli_args.use_cache
    hide_failed = cli_args.hide_failed

    # DEVICE LOADING #####
    devices = obtain_devices(device_or_group)

    # Retrieve output from devices
    my_files = []
    failed_devices = []
    results = {}
    if not use_cached_files:

        # UPDATE DEVICE PARAMS (WITH CLI ARGS) / Create Task List #####
        device_tasks = []
        for device_name, device_params in devices.items():
            update_device_params(
                device_params,
                username=cli_username,
                password=cli_password,
                secret=cli_secret,
            )
            if not cmd_arg:
                device_type = device_params["device_type"]
                cli_command = SHOW_RUN_MAPPER.get(device_type, "show run")
            device_tasks.append(
                {
                    "device_name": device_name,
                    "device_params": device_params,
                    "cli_command": cli_command,
                }
            )

        # THREADING #####
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(ssh_conn, **kwargs) for kwargs in device_tasks]
            for future in as_completed(futures):
                device_name, output = future.result()
                results[device_name] = output

        netmiko_base_dir, netmiko_full_dir = find_netmiko_dir()
        ensure_dir_exists(netmiko_base_dir)
        ensure_dir_exists(netmiko_full_dir)
        for device_name, output in results.items():

            file_name = write_tmp_file(device_name, output)
            if ERROR_PATTERN not in output:
                my_files.append(file_name)
            else:
                failed_devices.append(device_name)
    else:
        for device_name in devices:
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
