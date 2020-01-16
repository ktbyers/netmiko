#!/usr/bin/env python
import pytest
from netmiko import file_transfer

# def test_enable_scp(scp_fixture):
#    ssh_conn, scp_transfer = scp_fixture
#
#    scp_transfer.disable_scp()
#    output = ssh_conn.send_command_expect("show run | inc scp")
#    assert 'ip scp server enable' not in output
#
#    scp_transfer.enable_scp()
#    output = ssh_conn.send_command_expect("show run | inc scp")
#    assert 'ip scp server enable' in output


def test_scp_put(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    if scp_transfer.check_file_exists():
        assert False
    else:
        scp_transfer.put_file()
        assert scp_transfer.check_file_exists() is True


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
    assert scp_transfer.verify_space_available() is True
    # intentional make there not be enough space available
    scp_transfer.file_size = 100000000000
    assert scp_transfer.verify_space_available() is False


def test_remote_file_size(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    if not scp_transfer.check_file_exists():
        scp_transfer.put_file()
    remote_file_size = scp_transfer.remote_file_size()
    assert remote_file_size == 19


def test_md5_methods(scp_fixture):
    ssh_conn, scp_transfer = scp_fixture
    md5_value = "d8df36973ff832b564ad84642d07a261"

    remote_md5 = scp_transfer.remote_md5()
    assert remote_md5 == md5_value
    assert scp_transfer.compare_md5() is True


def test_disconnect(scp_fixture):
    """Terminate the SSH session."""
    ssh_conn, scp_transfer = scp_fixture
    ssh_conn.disconnect()


def test_verify_space_available_get(scp_fixture_get):
    ssh_conn, scp_transfer = scp_fixture_get
    assert scp_transfer.verify_space_available() is True
    # intentional make there not be enough space available
    scp_transfer.file_size = 100000000000000
    assert scp_transfer.verify_space_available() is False


def test_scp_get(scp_fixture_get):
    ssh_conn, scp_transfer = scp_fixture_get

    if scp_transfer.check_file_exists():
        # File should not already exist
        assert False
    else:
        scp_transfer.get_file()
        if scp_transfer.check_file_exists():
            assert True
        else:
            assert False


def test_md5_methods_get(scp_fixture_get):
    ssh_conn, scp_transfer = scp_fixture_get
    md5_value = "d8df36973ff832b564ad84642d07a261"
    local_md5 = scp_transfer.file_md5("test9.txt")
    assert local_md5 == md5_value
    assert scp_transfer.compare_md5() is True


def test_disconnect_get(scp_fixture_get):
    """Terminate the SSH session."""
    ssh_conn, scp_transfer = scp_fixture_get
    ssh_conn.disconnect()


def test_file_transfer(scp_file_transfer):
    """Test Netmiko file_transfer function."""
    ssh_conn, file_system = scp_file_transfer
    source_file = "test9.txt"
    dest_file = "test9.txt"
    direction = "put"

    transfer_dict = file_transfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        file_system=file_system,
        direction=direction,
        overwrite_file=True,
    )

    # No file on device at the beginning
    assert (
        transfer_dict["file_exists"]
        and transfer_dict["file_transferred"]
        and transfer_dict["file_verified"]
    )

    # File exists on device at this point
    transfer_dict = file_transfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        file_system=file_system,
        direction=direction,
        overwrite_file=True,
    )
    assert (
        transfer_dict["file_exists"]
        and not transfer_dict["file_transferred"]
        and transfer_dict["file_verified"]
    )

    # Don't allow a file overwrite (switch the source file, but same dest file name)
    source_file = "test2_src.txt"
    with pytest.raises(Exception):
        transfer_dict = file_transfer(
            ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            overwrite_file=False,
        )

    # Don't allow MD5 and file overwrite not allowed
    source_file = "test9.txt"
    with pytest.raises(Exception):
        transfer_dict = file_transfer(
            ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            disable_md5=True,
            file_system=file_system,
            direction=direction,
            overwrite_file=False,
        )

    # Don't allow MD5 (this will force a re-transfer)
    transfer_dict = file_transfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        disable_md5=True,
        file_system=file_system,
        direction=direction,
        overwrite_file=True,
    )
    assert (
        transfer_dict["file_exists"]
        and transfer_dict["file_transferred"]
        and not transfer_dict["file_verified"]
    )

    # Transfer 'test2.txt' in preparation for get operations
    source_file = "test2_src.txt"
    dest_file = "test2.txt"
    transfer_dict = file_transfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        file_system=file_system,
        direction=direction,
        overwrite_file=True,
    )
    assert transfer_dict["file_exists"]

    # GET Operations
    direction = "get"
    source_file = "test9.txt"
    dest_file = "testx.txt"
    transfer_dict = file_transfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        disable_md5=False,
        file_system=file_system,
        direction=direction,
        overwrite_file=True,
    )
    # File get should occur here
    assert (
        transfer_dict["file_exists"]
        and transfer_dict["file_transferred"]
        and transfer_dict["file_verified"]
    )

    # File should exist now
    transfer_dict = file_transfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        disable_md5=False,
        file_system=file_system,
        direction=direction,
        overwrite_file=True,
    )
    assert (
        transfer_dict["file_exists"]
        and not transfer_dict["file_transferred"]
        and transfer_dict["file_verified"]
    )

    # Don't allow a file overwrite (switch the file, but same dest file name)
    source_file = "test2.txt"
    dest_file = "testx.txt"
    with pytest.raises(Exception):
        transfer_dict = file_transfer(
            ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            overwrite_file=False,
        )

    # Don't allow MD5 and file overwrite not allowed
    source_file = "test9.txt"
    dest_file = "testx.txt"
    with pytest.raises(Exception):
        transfer_dict = file_transfer(
            ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            disable_md5=True,
            file_system=file_system,
            direction=direction,
            overwrite_file=False,
        )

    # Don't allow MD5 (this will force a re-transfer)
    transfer_dict = file_transfer(
        ssh_conn,
        source_file=source_file,
        dest_file=dest_file,
        disable_md5=True,
        file_system=file_system,
        direction=direction,
        overwrite_file=True,
    )
    assert (
        transfer_dict["file_exists"]
        and transfer_dict["file_transferred"]
        and not transfer_dict["file_verified"]
    )
