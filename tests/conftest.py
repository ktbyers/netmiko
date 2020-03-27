#!/usr/bin/env python
"""py.test fixtures to be used in netmiko test suite."""
from os import path
import os

import pytest

from netmiko import ConnectHandler, FileTransfer, InLineTransfer, SSHDetect
from tests.test_utils import parse_yaml


PWD = path.dirname(path.realpath(__file__))


def pytest_addoption(parser):
    """Add test_device option to py.test invocations."""
    parser.addoption(
        "--test_device",
        action="store",
        dest="test_device",
        type=str,
        help="Specify the platform type to test on",
    )


@pytest.fixture(scope="module")
def net_connect(request):
    """
    Create the SSH connection to the remote device

    Return the netmiko connection object
    """
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    conn = ConnectHandler(**device)
    return conn


@pytest.fixture(scope="module")
def net_connect_cmd_verify(request):
    """
    Create the SSH connection to the remote device

    Return the netmiko connection object

    Set global_cmd_verify = False
    """
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    device["global_cmd_verify"] = False
    conn = ConnectHandler(**device)
    return conn


@pytest.fixture(scope="function")
def net_connect_newconn(request):
    """
    Create the SSH connection to the remote device

    Return the netmiko connection object.
    Force a new connection for each test.
    """
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    conn = ConnectHandler(**device)
    return conn


@pytest.fixture()
def net_connect_cm(request):
    """
    Create the SSH connection to the remote device using a context manager
    retrieve the find_prompt() data and close the connection.
    """
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    my_prompt = ""
    with ConnectHandler(**device) as conn:
        my_prompt = conn.find_prompt()
    return my_prompt


@pytest.fixture(scope="module")
def net_connect_slog_wr(request):
    """
    Create the SSH connection to the remote device. Modify session_log init arguments.

    Return the netmiko connection object.
    """
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    # Overwrite default session_log location
    device["session_log"] = "SLOG/cisco881_slog_wr.log"
    device["session_log_record_writes"] = True
    conn = ConnectHandler(**device)
    return conn


@pytest.fixture(scope="module")
def device_slog(request):
    """
    Create the SSH connection to the remote device. Modify session_log init arguments.

    Return the netmiko device (not connected)
    """
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    device["session_log_file_mode"] = "append"
    return device


@pytest.fixture(scope="module")
def expected_responses(request):
    """
    Parse the responses.yml file to get a responses dictionary
    """
    device_under_test = request.config.getoption("test_device")
    responses = parse_yaml(PWD + "/etc/responses.yml")
    return responses[device_under_test]


@pytest.fixture(scope="module")
def commands(request):
    """
    Parse the commands.yml file to get a commands dictionary
    """
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    test_platform = device["device_type"]

    commands_yml = parse_yaml(PWD + "/etc/commands.yml")
    return commands_yml[test_platform]


def delete_file_nxos(ssh_conn, dest_file_system, dest_file):
    """
    nxos1# delete bootflash:test2.txt
    Do you want to delete "/test2.txt" ? (yes/no/abort)   [y] y
    """
    if not dest_file_system:
        raise ValueError("Invalid file system specified")
    if not dest_file:
        raise ValueError("Invalid dest file specified")

    full_file_name = "{}{}".format(dest_file_system, dest_file)

    cmd = "delete {}".format(full_file_name)
    output = ssh_conn.send_command_timing(cmd)
    if "yes/no/abort" in output and dest_file in output:
        output += ssh_conn.send_command_timing(
            "y", strip_command=False, strip_prompt=False
        )
        return output
    else:
        output += ssh_conn.send_command_timing("abort")
    raise ValueError("An error happened deleting file on Cisco NX-OS")


def delete_file_ios(ssh_conn, dest_file_system, dest_file):
    """Delete a remote file for a Cisco IOS device."""
    if not dest_file_system:
        raise ValueError("Invalid file system specified")
    if not dest_file:
        raise ValueError("Invalid dest file specified")

    full_file_name = f"{dest_file_system}/{dest_file}"

    cmd = f"delete {full_file_name}"
    output = ssh_conn.send_command_timing(cmd, delay_factor=2)
    if "Delete" in output and dest_file in output:
        output += ssh_conn.send_command_timing("\n", delay_factor=2)
        if "Delete" in output and full_file_name in output and "confirm" in output:
            output += ssh_conn.send_command_timing("y", delay_factor=2)
            return output
        else:
            output += ssh_conn.send_command_timing("n", delay_factor=2)

    raise ValueError("An error happened deleting file on Cisco IOS")


def delete_file_dellos10(ssh_conn, dest_file_system, dest_file):
    """Delete a remote file for a Dell OS10 device."""
    if not dest_file:
        raise ValueError("Invalid dest file specified")

    cmd = "delete home://{}".format(dest_file)
    output = ssh_conn.send_command_timing(cmd)
    if "Proceed to delete" in output:
        output = ssh_conn.send_command_timing("yes")
        return output

    raise ValueError("An error happened deleting file on Dell OS10")


def delete_file_generic(ssh_conn, dest_file_system, dest_file):
    """Delete a remote file for a Junos device."""
    full_file_name = "{}/{}".format(dest_file_system, dest_file)
    cmd = "rm {}".format(full_file_name)
    output = ssh_conn._enter_shell()
    output += ssh_conn.send_command_timing(cmd, strip_command=False, strip_prompt=False)
    output += ssh_conn._return_cli()
    return output


def delete_file_ciena_saos(ssh_conn, dest_file_system, dest_file):
    """Delete a remote file for a ciena device."""
    full_file_name = "{}/{}".format(dest_file_system, dest_file)
    cmd = "file rm {}".format(full_file_name)
    output = ssh_conn.send_command_timing(cmd, strip_command=False, strip_prompt=False)
    return output


@pytest.fixture(scope="module")
def scp_fixture(request):
    """
    Create an FileTransfer object.

    Return a tuple (ssh_conn, scp_handle)
    """
    platform_args = get_platform_args()

    # Create the files
    with open("test9.txt", "w") as f:
        # Not important what it is in the file
        f.write("no logging console\n")

    with open("test2_src.txt", "w") as f:
        # Not important what it is in the file
        f.write("no logging console\n")
        f.write("logging buffered 10000\n")

    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    ssh_conn = ConnectHandler(**device)

    platform = device["device_type"]
    dest_file_system = platform_args[platform]["file_system"]
    if "ciena_saos" in platform and ssh_conn.username:
        dest_file_system = f"/tmp/users/{ssh_conn.username}"

    source_file = "test9.txt"
    dest_file = "test9.txt"
    local_file = "testx.txt"
    direction = "put"

    scp_transfer = FileTransfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        file_system=dest_file_system,
        direction=direction,
    )
    scp_transfer.establish_scp_conn()

    # Make sure SCP is enabled
    if platform_args[platform]["enable_scp"]:
        scp_transfer.enable_scp()

    # Delete the test transfer files
    if scp_transfer.check_file_exists():
        func = platform_args[platform]["delete_file"]
        func(ssh_conn, dest_file_system, dest_file)
    if os.path.exists(local_file):
        os.remove(local_file)
    return (ssh_conn, scp_transfer)


@pytest.fixture(scope="module")
def scp_fixture_get(request):
    """
    Create an FileTransfer object (direction=get)

    Return a tuple (ssh_conn, scp_handle)
    """
    platform_args = get_platform_args()
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    ssh_conn = ConnectHandler(**device)

    platform = device["device_type"]
    dest_file_system = platform_args[platform]["file_system"]
    source_file = "test9.txt"
    local_file = "testx.txt"
    dest_file = local_file
    direction = "get"

    scp_transfer = FileTransfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        file_system=dest_file_system,
        direction=direction,
    )
    scp_transfer.establish_scp_conn()

    # Make sure SCP is enabled
    if platform_args[platform]["enable_scp"]:
        scp_transfer.enable_scp()

    # Delete the test transfer files
    if os.path.exists(local_file):
        os.remove(local_file)
    return (ssh_conn, scp_transfer)


@pytest.fixture(scope="module")
def tcl_fixture(request):
    """
    Create an InLineTransfer object.

    Return a tuple (ssh_conn, tcl_handle)
    """
    # Create the files
    with open("test9.txt", "w") as f:
        # Not important what it is in the file
        f.write("no logging console\n")

    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    ssh_conn = ConnectHandler(**device)

    dest_file_system = "flash:"
    source_file = "test9.txt"
    dest_file = "test9.txt"
    local_file = "testx.txt"
    direction = "put"

    tcl_transfer = InLineTransfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        file_system=dest_file_system,
        direction=direction,
    )

    # Delete the test transfer files
    if tcl_transfer.check_file_exists():
        delete_file_ios(ssh_conn, dest_file_system, dest_file)
    if os.path.exists(local_file):
        os.remove(local_file)

    return (ssh_conn, tcl_transfer)


@pytest.fixture(scope="module")
def ssh_autodetect(request):
    """Create an SSH autodetect object.

    return (ssh_conn, real_device_type)
    """
    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    my_device_type = device.pop("device_type")
    device["device_type"] = "autodetect"
    conn = SSHDetect(**device)
    return (conn, my_device_type)


@pytest.fixture(scope="module")
def scp_file_transfer(request):
    """
    Testing file_transfer

    Return the netmiko connection object
    """
    platform_args = get_platform_args()

    # Create the files
    with open("test9.txt", "w") as f:
        # Not important what it is in the file
        f.write("no logging console\n")

    with open("test2_src.txt", "w") as f:
        # Not important what it is in the file
        f.write("no logging console\n")
        f.write("logging buffered 10000\n")

    device_under_test = request.config.getoption("test_device")
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device["verbose"] = False
    ssh_conn = ConnectHandler(**device)

    platform = device["device_type"]
    file_system = platform_args[platform]["file_system"]
    source_file = "test9.txt"
    dest_file = "test9.txt"
    local_file = "testx.txt"
    alt_file = "test2.txt"
    direction = "put"

    scp_transfer = FileTransfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        file_system=file_system,
        direction=direction,
    )
    scp_transfer.establish_scp_conn()

    # Delete the test transfer files
    if scp_transfer.check_file_exists():
        func = platform_args[platform]["delete_file"]
        func(ssh_conn, file_system, dest_file)
    if os.path.exists(local_file):
        os.remove(local_file)
    if os.path.exists(alt_file):
        os.remove(alt_file)

    return (ssh_conn, file_system)


def get_platform_args():
    return {
        "cisco_ios": {
            "file_system": "flash:",
            "enable_scp": True,
            "delete_file": delete_file_ios,
        },
        "juniper_junos": {
            "file_system": "/var/tmp",
            "enable_scp": False,
            "delete_file": delete_file_generic,
        },
        "arista_eos": {
            "file_system": "/mnt/flash",
            "enable_scp": False,
            "delete_file": delete_file_generic,
        },
        "cisco_nxos": {
            "file_system": "bootflash:",
            "enable_scp": False,
            "delete_file": delete_file_nxos,
        },
        "cisco_xr": {
            "file_system": "disk0:",
            "enable_scp": False,
            # Delete pattern is the same on IOS-XR
            "delete_file": delete_file_ios,
        },
        "linux": {
            "file_system": "/var/tmp",
            "enable_scp": False,
            "delete_file": delete_file_generic,
        },
        "dellos10": {
            "file_system": "/home/admin",
            "enable_scp": False,
            "delete_file": delete_file_dellos10,
        },
        "ciena_saos": {
            "file_system": "/tmp/users/ciena",
            "enable_scp": False,
            "delete_file": delete_file_ciena_saos,
        },
    }
