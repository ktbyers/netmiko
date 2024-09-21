#!/usr/bin/env python
"""Return output from single show cmd using Netmiko."""
import argparse
import sys
import os
import subprocess
from datetime import datetime
from getpass import getpass
from concurrent.futures import ThreadPoolExecutor, as_completed

from netmiko.utilities import load_devices, display_inventory
from netmiko.utilities import find_netmiko_dir
from netmiko.cli_tools import ERROR_PATTERN, GREP, MAX_WORKERS, __version__
from netmiko.cli_tools.cli_helpers import obtain_devices, update_device_params, ssh_conn
from netmiko.cli_tools.outputters import output_dispatcher, output_failed_devices


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
    description = "Execute single config cmd using Netmiko"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "devices",
        nargs="?",
        help="Device or group to connect to",
        action="store",
        type=str,
    )
    parser.add_argument(
        "--infile", help="Read commands from file", type=argparse.FileType("r")
    )
    parser.add_argument(
        "--cmd",
        help="Config command to execute",
        action="store",
        default=None,
        type=str,
    )
    parser.add_argument("--username", help="Username", action="store", type=str)
    parser.add_argument("--password", help="Password", action="store_true")
    parser.add_argument("--secret", help="Enable Secret", action="store_true")
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
        "--json", help="Output results in JSON format", action="store_true"
    )
    parser.add_argument("--raw", help="Display raw output", action="store_true")
    parser.add_argument("--version", help="Display version", action="store_true")
    cli_args = parser.parse_args(args)
    if not cli_args.list_devices and not cli_args.version:
        if not cli_args.devices:
            parser.error("Devices not specified.")
        if not cli_args.cmd and not cli_args.infile:
            parser.error("No configuration commands provided.")
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
        print("netmiko-cfg v{}".format(__version__))
        return 0
    list_devices = cli_args.list_devices
    if list_devices:
        my_devices = load_devices()
        display_inventory(my_devices)
        return 0

    output_json = cli_args.json
    output_raw = cli_args.raw
    cfg_command = cli_args.cmd
    if cfg_command:
        if r"\n" in cfg_command:
            cfg_command = cfg_command.strip()
            cfg_command = cfg_command.split(r"\n")
    elif input:
        command_data = cli_args.infile.read()
        command_data = command_data.strip()
        cfg_command = command_data.splitlines()
    else:
        raise ValueError("No configuration commands provided.")
    device_or_group = cli_args.devices.strip()
    hide_failed = cli_args.hide_failed

    # DEVICE LOADING #####
    devices = obtain_devices(device_or_group)

    # Retrieve output from devices
    failed_devices = []
    results = {}

    # UPDATE DEVICE PARAMS (WITH CLI ARGS) / Create Task List #####
    device_tasks = []
    for device_name, device_params in devices.items():
        update_device_params(
            device_params,
            username=cli_username,
            password=cli_password,
            secret=cli_secret,
        )
        device_tasks.append(
            {
                "device_name": device_name,
                "device_params": device_params,
                "cfg_command": cfg_command,
            }
        )

    # THREADING #####
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(ssh_conn, **kwargs) for kwargs in device_tasks]
        for future in as_completed(futures):
            device_name, output = future.result()
            results[device_name] = output

    # FIND FAILED DEVICES #####
    # NEED NEW WAY TO CACHE AND RE-USE CACHED FILES
    valid_results = {}
    for device_name, output in results.items():
        # Cache output(?)
        # file_name = write_tmp_file(device_name, output)
        if ERROR_PATTERN in output:
            failed_devices.append(device_name)
            continue
        valid_results[device_name] = output

    # OUTPUT PROCESSING #####
    out_format = "text"
    if output_json and output_raw:
        out_format = "json_raw"
    elif output_json:
        out_format = "json"
    elif output_raw:
        out_format = "raw"
    # elif output_yaml:
    #    out_format = "yaml"
    output_dispatcher(out_format, valid_results)

    if cli_args.display_runtime:
        print("Total time: {0}".format(datetime.now() - start_time))

    if not hide_failed:
        output_failed_devices(failed_devices)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
