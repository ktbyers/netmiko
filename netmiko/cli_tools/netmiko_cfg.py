#!/usr/bin/env python
"""Return output from single show cmd using Netmiko."""
import sys
from datetime import datetime
from getpass import getpass
from concurrent.futures import ThreadPoolExecutor, as_completed

from netmiko.utilities import load_devices, display_inventory
from netmiko.cli_tools import ERROR_PATTERN, MAX_WORKERS, __version__
from netmiko.cli_tools.helpers import obtain_devices, update_device_params, ssh_conn
from netmiko.cli_tools.outputters import output_dispatcher, output_failed_devices
from netmiko.cli_tools.argument_handling import parse_arguments


COMMAND = "netmiko-cfg"


def main_ep():
    sys.exit(main(sys.argv[1:]))


def main(args):
    start_time = datetime.now()
    cli_args = parse_arguments(args, COMMAND)

    cli_username = cli_args.username if cli_args.username else None
    cli_password = getpass() if cli_args.password else None
    cli_secret = getpass("Enable secret: ") if cli_args.secret else None

    version = cli_args.version
    if version:
        print(f"{COMMAND} v{__version__}")
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
