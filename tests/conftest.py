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
    parser.addoption("--test_device", action="store", dest="test_device", type=str,
                     help="Specify the platform type to test on")

@pytest.fixture(scope='module')
def net_connect(request):
    """
    Create the SSH connection to the remote device

    Return the netmiko connection object
    """
    device_under_test = request.config.getoption('test_device')
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device['verbose'] = False
    conn = ConnectHandler(**device)
    return conn


@pytest.fixture()
def net_connect_cm(request):
    """
    Create the SSH connection to the remote device using a context manager 
    retrieve the find_prompt() data and close the connection.
    """
    device_under_test = request.config.getoption('test_device')
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device['verbose'] = False
    my_prompt = ""
    with ConnectHandler(**device) as conn:
        my_prompt = conn.find_prompt()
    return my_prompt


@pytest.fixture(scope='module')
def expected_responses(request):
    '''
    Parse the responses.yml file to get a responses dictionary
    '''
    device_under_test = request.config.getoption('test_device')
    responses = parse_yaml(PWD + "/etc/responses.yml")
    return responses[device_under_test]


@pytest.fixture(scope='module')
def commands(request):
    '''
    Parse the commands.yml file to get a commands dictionary
    '''
    device_under_test = request.config.getoption('test_device')
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    test_platform = device['device_type']

    commands_yml = parse_yaml(PWD + "/etc/commands.yml")
    return commands_yml[test_platform]


def delete_file_ios(ssh_conn, dest_file_system, dest_file):
    """Delete a remote file for a Cisco IOS device."""
    debug = False

    if not dest_file_system:
        raise ValueError("Invalid file system specified")
    if not dest_file:
        raise ValueError("Invalid dest file specified")

    # Check if the dest_file already exists
    full_file_name = "{0}/{1}".format(dest_file_system, dest_file)

    cmd = "delete {0}".format(full_file_name)
    output = ssh_conn.send_command_timing(cmd)
    if debug:
        print(output)
    if 'Delete' in output and dest_file in output:
        output += ssh_conn.send_command_timing("\n")
        if debug:
            print(output)
        if 'Delete' in output and full_file_name in output and 'confirm' in output:
            if debug:
                print("Deleting file.")
            output += ssh_conn.send_command_timing("y")
            return output
        else:
            output += ssh_conn.send_command_timing("n")

    raise ValueError("An error happened deleting file on Cisco IOS")


@pytest.fixture(scope='module')
def scp_fixture(request):
    """
    Create an FileTransfer object.

    Return a tuple (ssh_conn, scp_handle)
    """
    device_under_test = request.config.getoption('test_device')
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device['verbose'] = False
    ssh_conn = ConnectHandler(**device)

    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    local_file = 'testx.txt'
    direction = 'put'

    scp_transfer = FileTransfer(ssh_conn, source_file=source_file, dest_file=dest_file,
                                file_system=dest_file_system, direction=direction)
    scp_transfer.establish_scp_conn()

    # Make sure SCP is enabled
    scp_transfer.enable_scp()

    # Delete the test transfer files
    if scp_transfer.check_file_exists():
        delete_file_ios(ssh_conn, dest_file_system, dest_file)
    if os.path.exists(local_file):
        os.remove(local_file)

    return (ssh_conn, scp_transfer)

@pytest.fixture(scope='module')
def scp_fixture_get(request):
    """
    Create an FileTransfer object (direction=get)

    Return a tuple (ssh_conn, scp_handle)
    """
    device_under_test = request.config.getoption('test_device')
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device['verbose'] = False
    ssh_conn = ConnectHandler(**device)

    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    local_file = 'testx.txt'
    dest_file = local_file
    direction = 'get'

    scp_transfer = FileTransfer(ssh_conn, source_file=source_file, dest_file=dest_file,
                                file_system=dest_file_system, direction=direction)
    scp_transfer.establish_scp_conn()

    # Make sure SCP is enabled
    scp_transfer.enable_scp()

    # Delete the test transfer files
    if os.path.exists(local_file):
        os.remove(local_file)

    return (ssh_conn, scp_transfer)

@pytest.fixture(scope='module')
def tcl_fixture(request):
    """
    Create an InLineTransfer object.

    Return a tuple (ssh_conn, tcl_handle)
    """
    device_under_test = request.config.getoption('test_device')
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device['verbose'] = False
    ssh_conn = ConnectHandler(**device)

    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    local_file = 'testx.txt'
    direction = 'put'

    tcl_transfer = InLineTransfer(ssh_conn, source_file=source_file, dest_file=dest_file,
                                  file_system=dest_file_system, direction=direction)

    # Delete the test transfer files
    if tcl_transfer.check_file_exists():
        delete_file_ios(ssh_conn, dest_file_system, dest_file)
    if os.path.exists(local_file):
        os.remove(local_file)

    return (ssh_conn, tcl_transfer)

@pytest.fixture(scope='module')
def ssh_autodetect(request):
    """Create an SSH autodetect object. 

    return (ssh_conn, real_device_type)
    """
    device_under_test = request.config.getoption('test_device')
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device['verbose'] = False
    my_device_type = device.pop('device_type')
    device['device_type'] = 'autodetect'
    conn = SSHDetect(**device)
    return (conn, my_device_type)
