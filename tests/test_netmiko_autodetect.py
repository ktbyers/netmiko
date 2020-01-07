#!/usr/bin/env python
def test_ssh_connect(ssh_autodetect):
    """Verify the connection was established successfully."""
    net_conn, real_device_type = ssh_autodetect
    device_type = net_conn.autodetect()
    print(device_type)
    assert device_type == real_device_type
