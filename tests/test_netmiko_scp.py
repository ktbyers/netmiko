#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
import time
import sys
import os
from datetime import datetime
from getpass import getpass
from netmiko import ConnectHandler, FileTransfer
from netmiko import log

###def test_enable_scp(scp_fixture):
###    ssh_conn, scp_transfer = scp_fixture
###
###    scp_transfer.disable_scp()
###    output = ssh_conn.send_command_expect("show run | inc scp")
###    assert 'ip scp server enable' not in output
###
###    scp_transfer.enable_scp()
###    output = ssh_conn.send_command_expect("show run | inc scp")
###    assert 'ip scp server enable' in output

def test_scp_put(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    if scp_transfer.check_file_exists():
        assert False
    else:
        scp_transfer.put_file()
        assert scp_transfer.check_file_exists() == True

def test_remote_space_available(scp_fixture, expected_responses):
    ssh_conn, scp_transfer = scp_fixture
    remote_space = scp_transfer.remote_space_available()
    assert remote_space >= expected_responses["scp_remote_space"]
    
def test_local_space_available(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    local_space = scp_transfer.local_space_available()
    assert local_space >= 1000000000
    
def test_verify_space_available_put(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    assert scp_transfer.verify_space_available() == True
    # intentional make there not be enough space available
    scp_transfer.file_size = 10000000000
    assert scp_transfer.verify_space_available() == False

def test_remote_file_size(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    if not scp_transfer.check_file_exists():
        scp_transfer.put_file()
    remote_file_size = scp_transfer.remote_file_size()
    assert remote_file_size == 19

def test_md5_methods(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    md5_value = 'd8df36973ff832b564ad84642d07a261'

    remote_md5 = scp_transfer.remote_md5()
    assert remote_md5 == md5_value
    assert scp_transfer.compare_md5() == True

def test_disconnect(scp_fixture):
    """Terminate the SSH session."""
    ssh_conn, scp_transfer = scp_fixture
    ssh_conn.disconnect()

