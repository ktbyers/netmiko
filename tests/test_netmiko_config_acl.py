#!/usr/bin/env python
import ipaddress
import re


def test_large_acl(net_connect, acl_entries=100):
    """
    Test creating an ACL with tons of lines
    """
    base_cmd = {
        "cisco_xe": "ip access-list extended netmiko_test_large_acl",
        "cisco_ios": "ip access-list extended netmiko_test_large_acl",
        "cisco_nxos": "ip access-list netmiko_test_large_acl",
    }
    if net_connect.device_type not in ["cisco_xe", "cisco_ios", "cisco_nxos"]:
        return
    cmd = base_cmd[net_connect.device_type]
    net_connect.send_config_set(f"no {cmd}")
    cfg_lines = [cmd]

    # Generate sequence of ACL entries
    for i in range(1, acl_entries + 1):
        cfg_lines.append(
            f"permit ip host {ipaddress.ip_address('192.168.0.0') + i} any"
        )
    result = net_connect.send_config_set(cfg_lines)

    # send_config_set should return same num lines + four lines for entering/exiting cfg-mode
    # NX-OS is will have more than one newline (per line)
    result_list = re.split(r"\n+", result)
    assert len(result_list) == len(cfg_lines) + 4

    # Check that length of lines in show of the acl matches lines configured
    verify = net_connect.send_command("show ip access-lists netmiko_test_large_acl")
    verify_list = re.split(r"\n+", verify.strip())
    assert len(verify_list) == len(cfg_lines)
    net_connect.send_config_set(f"no {cmd}")
    net_connect.disconnect()
