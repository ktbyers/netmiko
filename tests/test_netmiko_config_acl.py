#!/usr/bin/env python
import ipaddress


def test_large_acl(net_connect, acl_entries=100):
    """
    Test creating an ACL with tons of lines
    """
    if net_connect.device_type not in ["cisco_xe", "cisco_ios"]:
        return
    net_connect.send_config_set(["no ip access-list extended netmiko_test_large_acl"])
    cfg_lines = ["ip access-list extended netmiko_test_large_acl"]
    for i in range(1, acl_entries + 1):
        cfg_lines.append(
            f"permit ip host {ipaddress.ip_address('192.168.0.0') + i} any"
        )
    result = net_connect.send_config_set(cfg_lines)
    # check that the result of send_config_set returns same num lines + four lines for getting
    # into and out of config mode
    assert len(result.splitlines()) == len(cfg_lines) + 4
    verify = net_connect.send_command("show ip access-lists netmiko_test_large_acl")
    # check that length of lines in show of the acl matches lines configured
    assert len(verify.lstrip().splitlines()) == len(cfg_lines)
    net_connect.send_config_set(["no ip access-list extended netmiko_test_large_acl"])
    net_connect.disconnect()
