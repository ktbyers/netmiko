#!/usr/bin/env python
"""
py.test fixtures to be used in netmiko test suite
"""

from os import path
import pytest

from netmiko import ConnectHandler
from tests.test_utils import parse_yaml


PWD = path.dirname(path.realpath(__file__))


def pytest_addoption(parser):
    '''
    Add test_device option to py.test invocations
    '''
    parser.addoption("--test_device", action="store", dest="test_device", type=str,
                     help="Specify the platform type to test on")


@pytest.fixture(scope='module')
def net_connect(request):
    '''
    Create the SSH connection to the remote device

    Return the netmiko connection object
    '''

    device_under_test = request.config.getoption('test_device')

    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device['verbose'] = False

    conn = ConnectHandler(**device)

    return conn


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


