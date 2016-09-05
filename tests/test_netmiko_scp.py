#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
import time
import sys
import os
from datetime import datetime
from getpass import getpass
from netmiko import ConnectHandler, FileTransfer

@pytest.fixture()
def test_delete_file(net_connect):
    """
    Delete the remote file

    pynet-rtr1#del flash:/test9.txt
    Delete filename [test9.txt]? 
    Delete flash:/test9.txt? [confirm]y
    """
    debug = False
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    direction = 'put'

    # Check if the dest_file already exists
    full_file_name = "{}/{}".format(dest_file_system, dest_file)
    cmd = "dir {}".format(full_file_name)
    output = net_connect.send_command_expect(cmd)
    if debug:
        print(output)

    if not '%Error opening' in output:
        # Delete the remote file
        cmd = "delete {}".format(full_file_name)
        output = net_connect.send_command_timing(cmd)
        if debug:
            print(output)
        if 'Delete filename' in output and dest_file in output:
            output = net_connect.send_command_timing("\n")
            if debug:
                print(output)
            if 'Delete' in output and full_file_name in output and 'confirm' in output:
                if debug:
                    print("Deleting file.")
                output = net_connect.send_command_timing("y")
                assert True == True
            else:
                output = net_connect.send_command_timing("n")
                assert True == False
            if debug:
                print(output)
    else:
        # Remote file doesn't exist
        if debug:
            print("File doesn't exist.")
        assert True == True
    return net_connect

def test_delete_local_file():
    """Delete local file."""
    local_file = 'testx.txt'
    if os.path.exists(local_file):
        os.remove(local_file)
        assert os.path.exists(local_file) == False
    else:
        # local file doesn't exist
        assert True == True

def test_scp_put(net_connect, commands, expected_responses):
    """SCP transfer file to remote file system."""
    debug = False
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    direction = 'put'

    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
        if scp_transfer.check_file_exists():
            if debug:
                print("File already exists")
            # File should not already exist
            assert False == True
        else:
            scp_transfer.put_file()
            if scp_transfer.check_file_exists():
                assert True == True
            else:
                assert False == True

def test_remote_space_available(net_connect, commands, expected_responses):
    debug = False
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    direction = 'put'

    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
        remote_space = scp_transfer.remote_space_available()
        assert remote_space >= 30000000
    
def test_local_space_available(net_connect, commands, expected_responses):
    debug = False
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    direction = 'get'

    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
        local_space = scp_transfer.local_space_available()
        assert local_space >= 1000000000
    
def test_verify_space_available(net_connect, commands, expected_responses):
    debug = False
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'

    direction = 'put'
    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
        assert scp_transfer.verify_space_available() == True
        # intentional make there not be enough space available
        scp_transfer.file_size = 1000000000
        assert scp_transfer.verify_space_available() == False

    direction = 'get'
    with FileTransfer(net_connect, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system, direction=direction) as scp_transfer:
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

