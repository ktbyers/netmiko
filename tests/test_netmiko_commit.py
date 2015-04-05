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

def retrieve_commands(commands):
    """
    Retrieve context needed for a set of commit actions
    """

    config_commands = commands['config']
    support_commit = commands.get('support_commit')
    config_verify = commands['config_verification']

    return (config_commands, support_commit, config_verify)


def setup_initial_state(net_connect, commands, expected_responses):
    '''
    Setup initial configuration prior to change so that config change can be verified
    '''

    # Setup initial state
    config_commands, support_commit, config_verify = retrieve_commands(commands)
    setup_base_config(net_connect, config_commands[0:1])

    cmd_response = expected_responses.get('cmd_response_init', config_commands[0])
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
    '''
    Send verify_cmd down channel, verify cmd_response in output
    '''

    config_commands_output = net_connect.send_command(verify_cmd)
    if cmd_response in config_commands_output:
        return True
    else:
        return False


def test_ssh_connect(net_connect, commands, expected_responses):
    '''
    Verify the connection was established successfully
    '''
    show_version = net_connect.send_command(commands["version"])
    assert expected_responses["version_banner"] in show_version


def test_config_mode(net_connect, commands, expected_responses):
    '''
    Test enter config mode
    '''
    net_connect.config_mode()
    assert net_connect.check_config_mode() == True

  
def test_commit_base(net_connect, commands, expected_responses):
    '''
    Test .commit() with no options
    '''

    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(net_connect,
        commands, expected_responses)

    # Perform commit test
    net_connect.send_config_set(config_commands)
    net_connect.commit()

    cmd_response = expected_responses.get('cmd_response_final', config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True


def test_commit_confirm(net_connect, commands, expected_responses):
    '''
    Test confirm with confirm
    '''
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(net_connect,
        commands, expected_responses)

    # Perform commit-confirm test
    net_connect.send_config_set(config_commands)
    net_connect.commit(confirm=True)

    cmd_response = expected_responses.get('cmd_response_final', config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

    # Perform confirm
    net_connect.commit()


def test_confirm_delay(net_connect, commands, expected_responses):
    '''
    Test commit with confirm and non-default delay
    '''
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(net_connect,
        commands, expected_responses)

    # Perform commit-confirm test
    net_connect.send_config_set(config_commands)
    net_connect.commit(confirm=True, confirm_delay=5)

    cmd_response = expected_responses.get('cmd_response_final', config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

    # Perform confirm
    net_connect.commit()


def test_no_confirm(net_connect, commands, expected_responses):
    '''
    Perform commit-confirm, but don't confirm (verify rollback)
    '''
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(net_connect,
        commands, expected_responses)

    # Perform commit-confirm test
    net_connect.send_config_set(config_commands)
    net_connect.commit(confirm=True, confirm_delay=1)

    cmd_response = expected_responses.get('cmd_response_final', config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

    time.sleep(190)

    # Verify rolled back to initial state
    cmd_response = expected_responses.get('cmd_response_init', config_commands[0])
    init_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert init_state is True


def test_commit_check(net_connect, commands, expected_responses):
    '''
    Test commit check
    '''
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(net_connect,
        commands, expected_responses)

    # Perform commit-confirm test
    net_connect.send_config_set(config_commands)
    net_connect.commit(check=True)

    # Verify at initial state
    cmd_response = expected_responses.get('cmd_response_init', config_commands[0])
    init_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert init_state is True

    rollback = commands.get('rollback')
    net_connect.send_config_set([rollback])


def test_commit_comment(net_connect, commands, expected_responses):
    '''
    Test commit with comment
    '''
    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(net_connect,
        commands, expected_responses)

    # Perform commit with comment
    net_connect.send_config_set(config_commands)
    net_connect.commit(comment="Unit test on commit with comment")

    # Verify change was committed
    cmd_response = expected_responses.get('cmd_response_final', config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

    # Verify commit comment
    commit_verification = commands.get("commit_verification")
    tmp_output = net_connect.send_command(commit_verification)
    commit_comment =  tmp_output.split("\n")[2]
    assert commit_comment.strip() in expected_responses.get("commit_comment")


def test_commit_andquit(net_connect, commands, expected_responses):
    '''
    Test commit and immediately quit configure mode
    '''

    # Setup the initial config state
    config_commands, support_commit, config_verify = setup_initial_state(net_connect,
        commands, expected_responses)

    # Execute change and commit
    net_connect.send_config_set(config_commands)
    net_connect.commit(and_quit=True)

    # Verify change was committed
    cmd_response = expected_responses.get('cmd_response_final', config_commands[-1])
    config_verify = 'show configuration | match archive'
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True

 
def test_exit_config_mode(net_connect, commands, expected_responses):
    '''
    Test exit config mode
    '''
    net_connect.exit_config_mode()
    assert net_connect.check_config_mode() == False 


def test_disconnect(net_connect, commands, expected_responses):
    '''
    Terminate the SSH session
    '''
    net_connect.disconnect()

