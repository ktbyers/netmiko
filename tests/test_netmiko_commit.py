#!/usr/bin/env python
"""
"""

def retrieve_commands(commands):
    """
    """

    config_commands = commands['config']
    support_commit = commands.get('support_commit')
    config_verify = commands['config_verification']

    return (config_commands, support_commit, config_verify)


def setup_initial_state(net_connect, verify_cmd, cmd_response):
    '''
    '''
    pass
   
 
def setup_base_config(net_connect, config_changes):
    """
    """
    net_connect.send_config_set(config_changes)
    net_connect.commit()


def config_change_verify(net_connect, verify_cmd, cmd_response):
    '''
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

    # Setup initial state
    config_commands, support_commit, config_verify = retrieve_commands(commands)
    setup_base_config(net_connect, config_commands[0:1])

    cmd_response = expected_responses.get('cmd_response_init', config_commands[0])
    initial_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert initial_state is True

    # Perform commit test
    net_connect.send_config_set(config_commands)
    net_connect.commit()

    cmd_response = expected_responses.get('cmd_response_final', config_commands[-1])
    final_state = config_change_verify(net_connect, config_verify, cmd_response)
    assert final_state is True


def test_commit_confirm(net_connect, commands, expected_responses):
    '''
    confirm
    '''
    pass


def test_confirm_delay(net_connect, commands, expected_responses):
    '''
    confirm delay
    '''
    pass


def test_commit_check(net_connect, commands, expected_responses):
    '''
    commit check
    '''
    pass


def test_commit_comment(net_connect, commands, expected_responses):
    '''
    commit check
    '''
    pass


def test_commit_andquit(net_connect, commands, expected_responses):
    '''
    '''
    pass

 
def test_exit_config_mode(net_connect, commands, expected_responses):
    '''
    Test exit config mode
    '''
    net_connect.exit_config_mode()
    assert net_connect.check_config_mode() == False 


#def test_manual_commit():
#    assert 'time-zone America/Los_Angeles' in manual_commit


#def test_edit_context_stripped():
#    '''
#    Verify [edit] is properly stripped for show commands in config mode
#    '''
#
#    assert '[edit' not in show_version_from_config
