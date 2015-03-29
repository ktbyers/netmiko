#!/usr/bin/env python
"""
py.test fixtures to be used in netmiko test suite
"""

from os import path
import pytest

from netmiko import ConnectHandler
from test_utils import parse_yaml


PWD = path.dirname(path.realpath(__file__))


def pytest_addoption(parser):
    '''
    Add test_platform option to py.test invocations
    '''
    parser.addoption("--test_platform", action="store", dest="test_platform", type=str,
                     help="Specify the platform type to test on")


@pytest.fixture(scope='module')
def net_connect(request):
    '''
    Create the SSH connection to the remote device
   
    Return the netmiko connection object 
    '''

    test_type = request.config.getoption('test_platform')

    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[test_type]
    device['verbose'] = False

    conn = ConnectHandler(**device)

    return conn


@pytest.fixture(scope='module')
def expected_responses(request):
    '''
    Parse the responses.yml file to get a responses dictionary
    '''
    test_type = request.config.getoption('test_platform')
    responses = parse_yaml(PWD + "/etc/responses.yml")
    return responses[test_type]


@pytest.fixture(scope='module')
def commands(request):
    '''
    Parse the commands.yml file to get a commands dictionary
    '''
    test_type = request.config.getoption('test_platform')
    commands = parse_yaml(PWD + "/etc/commands.yml")
    return commands[test_type]


