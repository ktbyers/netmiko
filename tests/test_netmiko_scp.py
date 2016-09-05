#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
import time
import sys
import os
from datetime import datetime
from getpass import getpass
from netmiko import ConnectHandler, FileTransfer

def test_enable_scp(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture

    scp_transfer.disable_scp()
    output = ssh_conn.send_command_expect("show run | inc scp")
    assert 'ip scp server enable' not in output

    scp_transfer.enable_scp()
    output = ssh_conn.send_command_expect("show run | inc scp")
    assert 'ip scp server enable' in output

def test_scp_put(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture

    if scp_transfer.check_file_exists():
        assert False
    else:
        scp_transfer.put_file()
        assert scp_transfer.check_file_exists() == True

def test_remote_space_available(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    remote_space = scp_transfer.remote_space_available()
    assert remote_space >= 30000000
    
def test_local_space_available(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    local_space = scp_transfer.local_space_available()
    assert local_space >= 1000000000
    
def test_verify_space_available_put(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    assert scp_transfer.verify_space_available() == True
    # intentional make there not be enough space available
    scp_transfer.file_size = 1000000000
    assert scp_transfer.verify_space_available() == False

def test_verify_space_available_get(scp_fixture_get):
    ssh_conn, scp_transfer = scp_fixture
    assert scp_transfer.verify_space_available() == True
    # intentional make there not be enough space available
    scp_transfer.file_size = 100000000000
    assert scp_transfer.verify_space_available() == False

def test_remote_file_size(net_connect, commands, expected_responses):
    debug = False
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    direction = 'get'

    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
        remote_file_size = scp_transfer.remote_file_size()
        assert remote_file_size == 19

def test_md5_methods(net_connect, commands, expected_responses):
    debug = False
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    direction = 'put'

    md5_value = 'd8df36973ff832b564ad84642d07a261'

    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
        local_md5 = scp_transfer.file_md5("test9.txt")
        assert local_md5 == md5_value
        remote_md5 = scp_transfer.remote_md5()
        assert remote_md5 == md5_value
        assert scp_transfer.compare_md5() == True

    direction = 'get'
    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
        assert scp_transfer.compare_md5() == True
    
def test_scp_get(net_connect, commands, expected_responses):
    debug = False
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'testx.txt'
    direction = 'get'

    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
        if scp_transfer.check_file_exists():
            if debug:
                print("File already exists")
            # File should not already exist
            assert False == True
        else:
            scp_transfer.get_file()
            if scp_transfer.check_file_exists():
                assert True == True
            else:
                assert False == True

