#!/usr/bin/env python
"""Create grep like remote behavior on show run or command output."""
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from netmiko.utilities import SHOW_RUN_MAPPER
from netmiko.cli_tools import ERROR_PATTERN, MAX_WORKERS, __version__
from netmiko.cli_tools.helpers import obtain_devices, update_device_params, ssh_conn
from netmiko.cli_tools.outputters import output_dispatcher, output_failed_devices
from netmiko.cli_tools.argument_handling import parse_arguments, extract_cli_vars


COMMAND = "netmiko-grep"


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
    out_format = "text_highlighted"
    if cli_args.json and cli_args.raw:
        out_format = "json_raw"
    elif cli_args.json:
        out_format = "json"
    elif cli_args.raw:
        out_format = "raw"
    # elif output_yaml:
    #    out_format = "yaml"
    output_dispatcher(out_format, valid_results, pattern=pattern)

    if cli_args.display_runtime:
        print("Total time: {0}".format(datetime.now() - start_time))

    if not hide_failed:
        output_failed_devices(failed_devices)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
