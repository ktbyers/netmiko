#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import concurrent.futures
import io
import os
from os import path
import sys
import traceback
import typing as t

import paramiko
import netmiko

__author__ = """Benjamin Kane"""
__version__ = '0.1.0'

__doc__ = """
Get info from Cisco NX-OS or IOS switches

Examples:

    net_mux.py device my-switch-hostname 'show run' 'show ver'
    net_mux.py files devicefile.txt commandfile.txt
    net_mux.py device --help
    net_mux.py files --help

Note: be careful to put any username/password/timeout/ssh_config_file
options before device/files arguments

    net_mux.py -u ben -p benpass device my-other-switch 'show clock'
"""


# https://github.com/ktbyers/netmiko/blob/0a9457d26c58df8ee8beb3a63ae5f0fd6dd9ead1/netmiko/base_connection.py#L588
def update_connection_with_ssh_config(ssh_config_file, dict_arg):
    """Update SSH connection parameters with contents of SSH 'config' file

    Stolen from netmiko
    """
    connect_dict = dict_arg.copy()

    # Use SSHConfig to generate source content.
    full_path = path.abspath(path.expanduser(ssh_config_file))
    if path.exists(full_path):
        ssh_config_instance = paramiko.SSHConfig()
        with io.open(full_path, "rt", encoding='utf-8') as f:
            ssh_config_instance.parse(f)
            source = ssh_config_instance.lookup(connect_dict['hostname'])
    else:
        source = {}

    if "proxycommand" in source:
        proxy = paramiko.ProxyCommand(source['proxycommand'])
    elif "ProxyCommand" in source:
        proxy = paramiko.ProxyCommand(source['ProxyCommand'])
    else:
        proxy = None

    # NOTE (bbkane): I don't have defaults, so I'm not sure if I need this
    # Only update 'hostname', 'sock', 'port', and 'username'
    # For 'port' and 'username' only update if using object defaults

    if 'port' not in connect_dict:
        connect_dict['port'] = 22

    if connect_dict['port'] == 22:
        connect_dict['port'] = int(source.get('port', 22))
    if connect_dict['username'] == '':
        connect_dict['username'] = source.get('username', connect_dict['username'])
    if proxy:
        connect_dict['sock'] = proxy
    connect_dict['hostname'] = source.get('hostname', connect_dict['hostname'])

    return connect_dict


def guess_device_type(device: str,
                      username: str,
                      password: str,
                      timeout: int = 90,
                      ssh_config_file=None) -> str:
    """return 'cisco_ios' or 'cisco_nxos'

    kwargs are passed on to paramikos's `.connect` method

    This uses a non-netmiko approach because we need
    the string to establish a connection for netmiko

    The biggest problem with it is it's only good
    for one commmand before the SSH session is invalid,
    so netmiko is definitely better for most things
    """

    device = {
        'hostname': device,
        'username': username,
        'password': password,
        'look_for_keys': False,
        'allow_agent': False,
        'timeout': timeout
    }

    if ssh_config_file:
        device = update_connection_with_ssh_config(ssh_config_file, device)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(**device)

    chan = ssh.get_transport().open_session()
    chan.get_pty()
    f = chan.makefile()

    chan.exec_command('show version')
    version_output = f.read().decode('utf-8')

    # TODO: add contextlib.closing here
    f.close()
    ssh.close()

    if 'Cisco IOS Software' in version_output:
        return 'cisco_ios'
    if 'Cisco Nexus Operating System' in version_output:
        return 'cisco_nxos'
    if 'Authorization failed' in version_output:
        raise ValueError('Authorization failed')
    if 'Cisco Internetwork Operating System Software' in version_output:
        if 'IOS' in version_output:
            return "cisco_ios"
        if 'NX-OS' in version_output:
            return 'cisco_nxos'
    raise ValueError(f"{device}: Unknown version: Output of `show version`:\n{version_output}")


def run_commands(device: str,
                 username: str,
                 password: str,
                 command_list: t.List[str],
                 timeout: int = 90,
                 device_type=None,
                 ssh_config_file=None) -> t.List[str]:
    """run commands on a device
    kwargs are passed on to `netmiko.ConnectHandler` and paramiko's `.connect` method"""

    if not device_type:
        device_type = guess_device_type(device, username, password, ssh_config_file=ssh_config_file)
    conn = netmiko.ConnectHandler(ip=device,
                                  username=username,
                                  password=password,
                                  timeout=timeout,
                                  device_type=device_type,
                                  ssh_config_file=ssh_config_file)

    with conn:
        return [conn.send_command(command)
                for command in command_list]


def parse_args(*args, **kwargs):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-u',
        '--username',
        help='Defaults to the value of NET_MUX_USER from the environment'
    )
    parser.add_argument(
        '-p',
        '--password',
        help='Defaults to the value of NET_MUX_PASS from the environment'
    )

    parser.add_argument(
        '-t',
        '--timeout',
        type=int,
        default=90
    )
    parser.add_argument(
        '--device_type',
        help="'cisco_ios' or 'cisco_nxos'. If not provided, we\'ll try to guess it"
    )

    parser.add_argument(
        '--ssh_config_file',
        help='Mostly for proxies'
    )

    subparsers = parser.add_subparsers(
        help='Modes of operations',
        dest='subparser',
        title='Sub-command'
    )

    file_parser = subparsers.add_parser(
        'files',
        help='Use files to run multiple commands on multiple devices'
    )
    file_parser.add_argument(
        'devicefile',
        help='File must contain a newline separated list of devices.'
             ' Lines starting with # are ignored'
    )
    file_parser.add_argument(
        'commandfile',
        help='File must contain a newline separated list of commands.'
             ' Lines starting with # are ignored'
    )
    file_parser.add_argument(
        '--processes',
        action='store_true',
        help='use processes instead of threads'
    )
    file_parser.add_argument(
        '--max_workers',
        type=int,
        default=None,
        help='Number of forks/processes'
    )

    file_parser.add_argument(
        '--prefix',
        type=str,
        default='',
        help='prefix to add to filenames. Each filename will be <prefix><device>.txt.'
             ' Useful if you want to attach a date or use `pre_` or `post_` for change type things'
    )

    command_parser = subparsers.add_parser(
        'device',
        help='Run multiple commands from one device'
    )
    command_parser.add_argument('device')
    command_parser.add_argument('commands', nargs='+')

    args = parser.parse_args(*args, **kwargs)
    try:
        args.username = args.username or os.environ['NET_MUX_USER']
    except KeyError:
        raise SystemExit('Either use the --username flag'
                         ' or export NET_MUX_USER in your environment')
    try:
        args.password = args.password or os.environ['NET_MUX_PASS']
    except KeyError:
        raise SystemExit('Either use the --password flag'
                         ' or export NET_MUX_PASS in your environment')

    return args


def parse_iterable(iterable, key=lambda l: l and not l.startswith('#'), strip_line=True):
    """
    Params:
        iterable of strings (a file or perhaps a string.split()). Each string will be stripped()
        key: function applied to iterable that determines what will be yielded
        strip_line: determines whether yielded line is stripped or not
    Return: str
    """
    for line in iterable:
        stripped_line = line.strip()
        if key(stripped_line):
            if strip_line:
                yield stripped_line
            else:
                yield line


DeviceToOutputGenerator = t.Generator[t.Tuple[str, t.List[str]], None, None]


def run_concurrent_commands(args: argparse.Namespace,
                            devices: t.Iterable[str],
                            commands: t.Iterable[str]) -> DeviceToOutputGenerator:
    """Run some concurrent commands with what we're passed

    Returns a generator of (device, outputs)
    """

    if args.processes:
        Executor = concurrent.futures.ProcessPoolExecutor
    else:
        Executor = concurrent.futures.ThreadPoolExecutor

    with Executor(max_workers=args.max_workers) as executor:
        future_to_device = {
            executor.submit(
                run_commands,
                device,
                args.username,
                args.password,
                commands,
                args.timeout,
                args.device_type,
                args.ssh_config_file
            ): device for device in devices
        }  # long lines yay...
        for future in concurrent.futures.as_completed(future_to_device):
            device = future_to_device[future]
            try:
                outputs = future.result()
            except Exception:
                traceback.print_exc(file=sys.stderr)
            else:
                # TODO: better API here?
                yield device, outputs


def main():
    args = parse_args()
    if args.subparser == 'files':
        with open(args.commandfile) as fp:
            commands = list(parse_iterable(fp))
        with open(args.devicefile) as fp:
            devices = list(parse_iterable(fp))
        for device, outputs in run_concurrent_commands(args, devices, commands):
            with open(f'{args.prefix}{device}.txt', 'w') as fp:
                for command, output in zip(commands, outputs):
                    print(f'# COMMAND: {command}', file=fp)
                    print(output, file=fp)

    elif args.subparser == 'device':
        outputs = run_commands(
            args.device,
            args.username,
            args.password,
            args.commands,
            args.timeout,
            args.device_type,
            args.ssh_config_file
        )
        for command, output in zip(args.commands, outputs):
            print(f'# COMMAND: {command}')
            print(output)
    else:
        raise SystemExit(f'Invalid subcommand: `{args.subparser}`. Try `--help`')


if __name__ == '__main__':
    main()
