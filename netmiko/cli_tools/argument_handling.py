import argparse


def common_args(parser):
    """Add common arguments to the parser."""
    parser.add_argument(
        "devices",
        nargs="?",
        help="Device or group to connect to",
        action="store",
        type=str,
    )
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
    pass


def cfg_args(parser):
    """Add arguments specific to netmiko_cfg.py."""
    parser.add_argument(
        "--infile", help="Read commands from file", type=argparse.FileType("r")
    )


def parse_arguments(args, command):
    """Parse command-line arguments for both scripts."""

    if command == "netmiko-cfg":
        description = "Execute configurations command using Netmiko"
        addl_args = cfg_args
    elif command == "netmiko-show":
        description = "Execute show command using Netmiko (defaults to 'show run')"
        addl_args = show_args
    elif command == "netmiko-grep":
        # FIX
        description = ""
        # addl_args = grep_args
    else:
        # FIX: better message
        raise ValueError()

    parser = argparse.ArgumentParser(description=description)
    common_args(parser)

    # Add additional arguments based (addl_args references a function)
    addl_args(parser)

    cli_args = parser.parse_args(args)
    if not cli_args.list_devices and not cli_args.version:
        if not cli_args.devices:
            parser.error("Devices not specified.")
        if command == "netmiko-cfg" and not cli_args.cmd and not cli_args.infile:
            parser.error("No configuration commands provided.")

    return cli_args
