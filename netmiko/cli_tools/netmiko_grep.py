#!/usr/bin/env python
"""Create grep like remote behavior on show run or command output."""
import sys
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from netmiko.utilities import write_tmp_file, ensure_dir_exists
from netmiko.utilities import find_netmiko_dir
from netmiko.utilities import SHOW_RUN_MAPPER
from netmiko.cli_tools import ERROR_PATTERN, GREP, MAX_WORKERS, __version__
from netmiko.cli_tools.helpers import obtain_devices, update_device_params, ssh_conn
from netmiko.cli_tools.argument_handling import parse_arguments, extract_cli_vars


COMMAND = "netmiko-grep"


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


def main_ep():
    sys.exit(main(sys.argv[1:]))


def main(args):
    start_time = datetime.now()

    # CLI ARGS #####
    cli_args = parse_arguments(args, COMMAND)
    cli_vars = extract_cli_vars(cli_args, command=COMMAND, __version__=__version__)
    cli_command = cli_args.cmd
    cmd_arg = False
    if cli_command:
        cmd_arg = True
    device_or_group = cli_args.devices.strip()
    hide_failed = cli_args.hide_failed
    pattern = cli_args.pattern

    # DEVICE LOADING #####
    devices = obtain_devices(device_or_group)

    # Retrieve output from devices
    my_files = []
    failed_devices = []
    results = {}

    # UPDATE DEVICE PARAMS (WITH CLI ARGS) #####
    device_tasks = []
    for device_name, device_params in devices.items():
        update_device_params(
            device_params,
            username=cli_vars["cli_username"],
            password=cli_vars["cli_password"],
            secret=cli_vars["cli_secret"],
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
