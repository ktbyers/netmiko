#!/usr/bin/env python
import re
import pytest
from network_utilities import generate_ios_acl
from network_utilities import generate_cisco_nxos_acl  # noqa
from network_utilities import generate_cisco_asa_acl  # noqa
from network_utilities import generate_cisco_xr_acl  # noqa
from network_utilities import generate_arista_eos_acl  # noqa
from network_utilities import generate_juniper_junos_acl  # noqa


def remove_acl(net_connect, cmd, commit=False):
    """Ensure ACL is removed."""
    net_connect.send_config_set(cmd)
    if commit:
        net_connect.commit()
        net_connect.exit_config_mode()


def test_large_acl(net_connect, commands, expected_responses, acl_entries=100):
    """Test configuring a large ACL."""
    if commands.get("config_long_acl"):
        acl_config = commands.get("config_long_acl")
        base_cmd = acl_config["base_cmd"]
        verify_cmd = acl_config["verify_cmd"]
        delete_cmd = acl_config.get("delete_cmd")
        offset = acl_config["offset"]
    else:
        pytest.skip("Platform not supported for ACL test")

    platform = net_connect.device_type
    support_commit = commands.get("support_commit")

    if "juniper_junos" in platform or "cisco_asa" in platform:
        cmd = delete_cmd
    else:
        cmd = f"no {base_cmd}"
    remove_acl(net_connect, cmd=cmd, commit=support_commit)

    # Generate the ACL
    platform = net_connect.device_type
    if "cisco_ios" in net_connect.device_type or "cisco_xe" in net_connect.device_type:
        cfg_lines = generate_ios_acl()
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
    verify = net_connect.send_command(verify_cmd, read_timeout=90)
    verify_list = re.split(r"\n+", verify.strip())

    # IOS-XR potentially has a timestamp on the show command
    if "UTC" in verify_list[0]:
        verify_list.pop(0)
    if "juniper_junos" in platform:
        offset = 6
        assert len(verify_list) - offset == len(cfg_lines)
    elif "cisco_asa" in platform:
        offset = 1
        assert len(verify_list) - offset == len(cfg_lines)
    else:
        assert len(verify_list) == len(cfg_lines)

    if "juniper_junos" in platform or "cisco_asa" in platform:
        cmd = delete_cmd
    else:
        cmd = f"no {base_cmd}"
    remove_acl(net_connect, cmd=cmd, commit=support_commit)
    net_connect.disconnect()
