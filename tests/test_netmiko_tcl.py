#!/usr/bin/env python
def test_tcl_put(tcl_fixture):
    ssh_conn, transfer = tcl_fixture
    if transfer.check_file_exists():
        assert False
    else:
        transfer._enter_tcl_mode()
        transfer.put_file()
        transfer._exit_tcl_mode()
        assert transfer.check_file_exists() is True


def test_remote_space_available(tcl_fixture):
    ssh_conn, transfer = tcl_fixture
    remote_space = transfer.remote_space_available()
    assert remote_space >= 30000000


def test_verify_space_available_put(tcl_fixture):
    ssh_conn, transfer = tcl_fixture
    assert transfer.verify_space_available() is True
    # intentional make there not be enough space available
    transfer.file_size = 1000000000
    assert transfer.verify_space_available() is False


def test_remote_file_size(tcl_fixture):
    ssh_conn, transfer = tcl_fixture
    remote_file_size = transfer.remote_file_size()
    assert remote_file_size == 20


def test_md5_methods(tcl_fixture):
    ssh_conn, transfer = tcl_fixture
    md5_value = "4313f1adae86a21117441b0a95d482a7"

    remote_md5 = transfer.remote_md5()
    assert remote_md5 == md5_value
    assert transfer.compare_md5() is True


def test_disconnect(tcl_fixture):
    """Terminate the SSH session."""
    ssh_conn, transfer = tcl_fixture
    ssh_conn.disconnect()
