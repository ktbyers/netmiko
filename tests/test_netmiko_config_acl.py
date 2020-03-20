#!/usr/bin/env python
import re
import pytest
from ipaddress import ip_address


def test_large_acl(net_connect, acl_entries=100):
    """
    Test creating an ACL with tons of lines
    """

    platforms = {
        "cisco_xe": {
            "base_cmd": "ip access-list extended netmiko_test_large_acl",
            "verify_cmd": "show ip access-lists netmiko_test_large_acl",
            "offset": 4,
        },
        "cisco_ios": {
            "base_cmd": "ip access-list extended netmiko_test_large_acl",
            "verify_cmd": "show ip access-lists netmiko_test_large_acl",
            "offset": 4,
        },
        "cisco_xr": {
            "base_cmd": "ipv4 access-list netmiko_test_large_acl",
            "verify_cmd": "show access-lists netmiko_test_large_acl",
            "offset": 3,
        },
        "cisco_nxos": {
            "base_cmd": "ip access-list netmiko_test_large_acl",
            "verify_cmd": "show ip access-lists netmiko_test_large_acl",
            "offset": 4,
        },
    }

    if net_connect.device_type not in platforms.keys():
        pytest.skip("Platform not supported for ACL test")
    cmd = platforms[net_connect.device_type]["base_cmd"]
    verify_cmd = platforms[net_connect.device_type]["verify_cmd"]
    offset = platforms[net_connect.device_type]["offset"]
    net_connect.send_config_set(f"no {cmd}")
    if "cisco_xr" in net_connect.device_type:
        net_connect.commit()
        net_connect.exit_config_mode()
    cfg_lines = [cmd]

    # Generate sequence of ACL entries
    for i in range(1, acl_entries + 1):
        if "cisco_xr" in net_connect.device_type:
            cmd = f"permit ipv4 host {ip_address('192.168.0.0') + i} any"
        else:
            cmd = f"permit ip host {ip_address('192.168.0.0') + i} any"
        cfg_lines.append(cmd)

    result = net_connect.send_config_set(cfg_lines)
    if "cisco_xr" in net_connect.device_type:
        net_connect.commit()
        net_connect.exit_config_mode()

    # send_config_set should return same num lines + offset lines for entering/exiting cfg-mode
    # NX-OS is will have more than one newline (per line)
    result_list = re.split(r"\n+", result)
    assert len(result_list) == len(cfg_lines) + offset

    # Check that length of lines in show of the acl matches lines configured
    verify = net_connect.send_command(verify_cmd)
    verify_list = re.split(r"\n+", verify.strip())
    # IOS-XR has a timestamp on the show command
    if "UTC" in verify_list[0]:
        verify_list.pop(0)
    assert len(verify_list) == len(cfg_lines)
    net_connect.send_config_set(f"no {cmd}")
    if "cisco_xr" in net_connect.device_type:
        net_connect.commit()
        net_connect.exit_config_mode()
    net_connect.disconnect()
