#!/usr/bin/env python
"""
test_ssh_connect: verify ssh connectivity
test_config_mode: verify enter config mode
test_commit_base: test std .commit()
test_commit_confirm: test commit with confirm
test_confirm_delay: test commit-confirm with non-std delay
test_no_confirm: test commit-confirm with no confirm
test_commit_check: test commit check
test_commit_comment: test commit with comment
test_commit_andquit: test commit andquit
test_exit_config_mode: verify exit config mode
test_disconnect: cleanly disconnect the SSH session
"""

import time
import re
import random
import string


def gen_random(N=6):
    return "".join(
        [
            random.choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for x in range(N)
        ]
    )


def retrieve_commands(commands):
    """
    Retrieve context needed for a set of commit actions
    """

    config_commands = commands["config"]
    support_commit = commands.get("support_commit")
    config_verify = commands["config_verification"]

    return (config_commands, support_commit, config_verify)


def setup_initial_state(net_connect, commands, expected_responses):
    """
    Setup initial configuration prior to change so that config change can be verified
    """

    # Setup initial state
    config_commands, support_commit, config_verify = retrieve_commands(commands)
    setup_base_config(net_connect, config_commands[0:1])

    cmd_response = expected_responses.get("cmd_response_init", config_commands[0])
    initial_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert initial_state is True

    return config_commands, support_commit, config_verify


def setup_base_config(net_connect, config_changes):
    """
    Send set of config commands and commit
    """
    net_connect.send_config_set(config_changes)
    net_connect.commit()


def config_change_verify(net_connect, verify_cmd, cmd_response):
    """
    Send verify_cmd down channel, verify cmd_response in output
    """
    config_commands_output = net_connect.send_command_expect(verify_cmd)
    if cmd_response in config_commands_output:
        return True
    else:
        return False


def test_ssh_connect(net_connect, commands, expected_responses):
    """
    Verify the connection was established successfully
    """
    show_version = net_connect.send_command_expect(commands["version"])
    assert expected_responses["version_banner"] in show_version


def test_config_mode(net_connect, commands, expected_responses):
    """
    Test enter config mode
    """
    net_connect.config_mode()
    assert net_connect.check_config_mode() is True


def test_commit_base(net_connect, commands, expected_responses):
    """
    Test .commit() with no options
    """
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(
        net_connect, commands, expected_responses
    )

    # Perform commit test
    net_connect.send_config_set(config_commands)
    net_connect.commit()

    cmd_response = expected_responses.get("cmd_response_final", config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True


def test_commit_confirm(net_connect, commands, expected_responses):
    """
    Test confirm with confirm
    """
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(
        net_connect, commands, expected_responses
    )

    # Perform commit-confirm test
    net_connect.send_config_set(config_commands)
    if net_connect.device_type == "cisco_xr":
        net_connect.commit(confirm=True, confirm_delay=60)
    else:
        net_connect.commit(confirm=True)

    cmd_response = expected_responses.get("cmd_response_final", config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

    # Perform confirm
    net_connect.commit()


def test_confirm_delay(net_connect, commands, expected_responses):
    """
    Test commit with confirm and non-default delay
    """
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(
        net_connect, commands, expected_responses
    )

    # Perform commit-confirm test
    net_connect.send_config_set(config_commands)
    if net_connect.device_type == "cisco_xr":
        net_connect.commit(confirm=True, confirm_delay=60)
    else:
        net_connect.commit(confirm=True, confirm_delay=5)

    cmd_response = expected_responses.get("cmd_response_final", config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

    # Perform confirm
    net_connect.commit()


def test_no_confirm(net_connect, commands, expected_responses):
    """
    Perform commit-confirm, but don't confirm (verify rollback)
    """
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(
        net_connect, commands, expected_responses
    )

    # Perform commit-confirm test
    net_connect.send_config_set(config_commands)
    if net_connect.device_type == "cisco_xr":
        net_connect.commit(confirm=True, confirm_delay=30)
    else:
        net_connect.commit(confirm=True, confirm_delay=1)

    cmd_response = expected_responses.get("cmd_response_final", config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

    time.sleep(130)

    # Verify rolled back to initial state
    cmd_response = expected_responses.get("cmd_response_init", config_commands[0])
    init_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert init_state is True


def test_clear_msg(net_connect, commands, expected_responses):
    """
    IOS-XR generates the following message upon a failed commit

    One or more commits have occurred from other
    configuration sessions since this session started
    or since the last commit was made from this session.
    You can use the 'show configuration commit changes'
    command to browse the changes.
    Do you wish to proceed with this commit anyway? [no]: yes

    Clear it
    """
    # Setup the initial config state
    config_commands, support_commit, config_verify = retrieve_commands(commands)

    if net_connect.device_type == "cisco_xr":
        output = net_connect.send_config_set(config_commands)
        output += net_connect.send_command_expect(
            "commit", expect_string=r"Do you wish to"
        )
        output += net_connect.send_command_expect("yes", auto_find_prompt=False)
    assert True is True


def test_commit_check(net_connect, commands, expected_responses):
    """
    Test commit check
    """
    # IOS-XR does not support commit check
    if net_connect.device_type == "cisco_xr":
        assert True is True
    else:

        # Setup the initial config state
        config_commands, support_commit, config_verify = setup_initial_state(
            net_connect, commands, expected_responses
        )

        # Perform commit-confirm test
        net_connect.send_config_set(config_commands)
        net_connect.commit(check=True)

        # Verify at initial state
        cmd_response = expected_responses.get("cmd_response_init", config_commands[0])
        init_state = config_change_verify(net_connect, config_verify, cmd_response)
        assert init_state is True

        rollback = commands.get("rollback")
        net_connect.send_config_set([rollback])


def test_commit_comment(net_connect, commands, expected_responses):
    """
    Test commit with comment
    """
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(
        net_connect, commands, expected_responses
    )

    # Perform commit with comment
    net_connect.send_config_set(config_commands)
    net_connect.commit(comment="Unit test on commit with comment")

    # Verify change was committed
    cmd_response = expected_responses.get("cmd_response_final", config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

    # Verify commit comment
    commit_verification = commands.get("commit_verification")
    tmp_output = net_connect.send_command(commit_verification)
    if net_connect.device_type == "cisco_xr":
        commit_comment = tmp_output
    else:
        commit_comment = tmp_output.strip().split("\n")[1]
    assert expected_responses.get("commit_comment") in commit_comment.strip()


def test_commit_andquit(net_connect, commands, expected_responses):
    """
    Test commit and immediately quit configure mode
    """

    # IOS-XR does not support commit and quit
    if net_connect.device_type == "cisco_xr":
        assert True is True
    else:

        # Setup the initial config state
        config_commands, support_commit, config_verify = setup_initial_state(
            net_connect, commands, expected_responses
        )

        # Execute change and commit
        net_connect.send_config_set(config_commands)
        net_connect.commit(and_quit=True)

        # Verify change was committed
        cmd_response = expected_responses.get("cmd_response_final", config_commands[-1])
        config_verify = "show configuration | match archive"
        final_state = config_change_verify(net_connect, config_verify, cmd_response)
        assert final_state is True


def test_commit_label(net_connect, commands, expected_responses):
    """Test commit label for IOS-XR."""

    if net_connect.device_type != "cisco_xr":
        assert True is True
    else:
        # Setup the initial config state
        config_commands, support_commit, config_verify = setup_initial_state(
            net_connect, commands, expected_responses
        )

        # Execute change and commit
        net_connect.send_config_set(config_commands)
        label = "test_lbl_" + gen_random()
        net_connect.commit(label=label)

        # Verify commit label
        commit_verification = commands.get("commit_verification")
        tmp_output = net_connect.send_command(commit_verification)
        match = re.search(r"Label: (.*)", tmp_output)
        response_label = match.group(1)
        response_label = response_label.strip()
        assert label == response_label


def test_commit_label_comment(net_connect, commands, expected_responses):
    """
    Test commit label for IOS-XR with comment
    """
    # IOS-XR only test
    if net_connect.device_type != "cisco_xr":
        assert True is True
    else:
        # Setup the initial config state
        config_commands, support_commit, config_verify = setup_initial_state(
            net_connect, commands, expected_responses
        )

        # Execute change and commit
        net_connect.send_config_set(config_commands)
        label = "test_lbl_" + gen_random()
        comment = "Test with comment and label"
        net_connect.commit(label=label, comment=comment)

        # Verify commit label
        commit_verification = commands.get("commit_verification")
        tmp_output = net_connect.send_command(commit_verification)
        match = re.search(r"Label: (.*)", tmp_output)
        response_label = match.group(1)
        response_label = response_label.strip()
        assert label == response_label
        match = re.search(r"Comment:  (.*)", tmp_output)
        response_comment = match.group(1)
        response_comment = response_comment.strip()
        response_comment = response_comment.strip('"')
        assert comment == response_comment


def test_commit_label_confirm(net_connect, commands, expected_responses):
    """
    Test commit label for IOS-XR with confirm
    """
    # IOS-XR only test
    if net_connect.device_type != "cisco_xr":
        assert True is True
    else:
        # Setup the initial config state
        config_commands, support_commit, config_verify = setup_initial_state(
            net_connect, commands, expected_responses
        )

        # Execute change and commit
        net_connect.send_config_set(config_commands)
        label = "test_lbl_" + gen_random()
        net_connect.commit(label=label, confirm=True, confirm_delay=120)

        cmd_response = expected_responses.get("cmd_response_final", config_commands[-1])
        final_state = config_change_verify(net_connect, config_verify, cmd_response)
        assert final_state is True

        # Verify commit label
        commit_verification = commands.get("commit_verification")
        tmp_output = net_connect.send_command(commit_verification)
        match = re.search(r"Label: (.*)", tmp_output)
        response_label = match.group(1)
        response_label = response_label.strip()
        assert label == response_label

        net_connect.commit()


def test_exit_config_mode(net_connect, commands, expected_responses):
    """
    Test exit config mode
    """
    net_connect.exit_config_mode()
    time.sleep(1)
    assert net_connect.check_config_mode() is False


def test_disconnect(net_connect, commands, expected_responses):
    """
    Terminate the SSH session
    """
    net_connect.disconnect()
