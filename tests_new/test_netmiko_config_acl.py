#!/usr/bin/env python
import re
import pytest
from network_utilities import generate_ios_acl, generate_nxos_acl
from network_utilities import generate_cisco_xr_acl  # noqa
from network_utilities import generate_arista_eos_acl  # noqa


def remove_acl(net_connect, cmd, commit=False):
    """Ensure ACL is removed."""
    net_connect.send_config_set(f"no {cmd}")
    if commit:
        net_connect.commit()
        net_connect.exit_config_mode()


def test_large_acl(net_connect, commands, expected_responses, acl_entries=100):
    """Test configuring a large ACL."""
    if commands.get("config_long_acl"):
        acl_config = commands.get("config_long_acl")
        base_cmd = acl_config["base_cmd"]
        verify_cmd = acl_config["verify_cmd"]
        offset = acl_config["offset"]
    else:
        pytest.skip("Platform not supported for ACL test")

    support_commit = commands.get("support_commit")
    remove_acl(net_connect, cmd=base_cmd, commit=support_commit)

    # Generate the ACL
    platform = net_connect.device_type
    if "cisco_ios" in net_connect.device_type or "cisco_xe" in net_connect.device_type:
        cfg_lines = generate_ios_acl()
    elif "cisco_nxos" in net_connect.device_type:
        cfg_lines = generate_nxos_acl()
    else:
        func_name = f"generate_{platform}_acl"
        acl_func = globals()[func_name]
        cfg_lines = acl_func()

    # Send ACL to remote devices
    result = net_connect.send_config_set(cfg_lines)
    if support_commit:
        net_connect.commit()
        net_connect.exit_config_mode()

    # send_config_set should return same num lines + offset lines for entering/exiting cfg-mode
    # NX-OS is will have more than one newline (per line)
    result_list = re.split(r"\n+", result)
    assert len(result_list) == len(cfg_lines) + offset

    # Check that length of lines in show of the acl matches lines configured
    verify = net_connect.send_command(verify_cmd)
    verify_list = re.split(r"\n+", verify.strip())

    # IOS-XR potentially has a timestamp on the show command
    if "UTC" in verify_list[0]:
        verify_list.pop(0)
    assert len(verify_list) == len(cfg_lines)

    remove_acl(net_connect, cmd=base_cmd, commit=support_commit)
    net_connect.disconnect()
