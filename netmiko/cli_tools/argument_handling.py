import sys
import argparse
from getpass import getpass
from netmiko.utilities import load_devices, display_inventory


def common_args(parser):
    """Add common arguments to the parser."""
    parser.add_argument(
        "--cmd",
        help="Command to execute",
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


def show_args(parser):
    """Add arguments specific to netmiko_show.py."""
    parser.add_argument(
        "devices",
        help="Device or group to connect to",
        action="store",
        type=str,
        nargs="?",
    )


def cfg_args(parser):
    """Add arguments specific to netmiko_cfg.py."""
    parser.add_argument(
        "devices",
        help="Device or group to connect to",
        action="store",
        type=str,
        nargs="?",
    )
    parser.add_argument(
        "--infile", help="Read commands from file", type=argparse.FileType("r")
    )


def grep_args(parser):
    """Add arguments specific to netmiko_grep.py."""
    parser.add_argument(
        "pattern", nargs="?", help="Pattern to search for", action="store", type=str
    )
    parser.add_argument(
        "devices",
        help="Device or group to connect to",
        action="store",
        type=str,
        nargs="?",
    )


def parse_arguments(args, command):
    """Parse command-line arguments for all scripts."""

    if command == "netmiko-cfg":
        description = "Execute configurations command using Netmiko"
        addl_args = cfg_args
    elif command == "netmiko-show":
        description = "Execute show command using Netmiko (defaults to 'show run')"
        addl_args = show_args
    elif command == "netmiko-grep":
        description = "Grep pattern search on Netmiko output (defaults to 'show run')"
        addl_args = grep_args
    else:
        raise ValueError(f"Unknown Netmiko cli-tool: {command}")

    parser = argparse.ArgumentParser(description=description)
    common_args(parser)

    # Add additional arguments based (addl_args references a function)
    addl_args(parser)

    cli_args = parser.parse_args(args)
    if not cli_args.list_devices and not cli_args.version:
        if not cli_args.devices:
            parser.error("Devices not specified.")
        elif command == "netmiko-cfg" and not cli_args.cmd and not cli_args.infile:
            parser.error("No configuration commands provided.")
        elif command == "netmiko-grep" and not cli_args.pattern:
            parser.error("Grep pattern not specified.")

    return cli_args


def extract_cli_vars(cli_args, command, __version__):

    return_vars = {}
    return_vars["cli_username"] = cli_args.username if cli_args.username else None
    return_vars["cli_password"] = getpass() if cli_args.password else None
    return_vars["cli_secret"] = getpass("Enable secret: ") if cli_args.secret else None
    version = cli_args.version
    if version:
        print(f"{command} v{__version__}")
        sys.exit(0)
    list_devices = cli_args.list_devices
    if list_devices:
        my_devices = load_devices()
        display_inventory(my_devices)
        sys.exit(0)

    return return_vars
