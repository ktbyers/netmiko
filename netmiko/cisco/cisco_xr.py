from __future__ import print_function
from __future__ import unicode_literals

import re

from netmiko.cisco_base_connection import CiscoBaseConnection


class CiscoXr(CiscoBaseConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established.
        When router in 'run' (linux $) prompt, switch back to XR prompt
        """
        self.set_base_prompt(alt_prompt_terminator='$')
        switch_to_xr_command = 'xr'
        if self.find_prompt().endswith('$'):
            self.send_command(switch_to_xr_command, expect_string='#')
            self.base_prompt = self.find_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')

    def config_mode(
            self,
            config_command='config term',
            pattern='',
            skip_check=True):
        """
        Enter into configuration mode on remote device.

        Cisco IOSXR devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            pattern = self.base_prompt[:16]
            pattern = self.current_prompt[:16]
        pattern = pattern + ".*config"
        return super(
            CiscoBaseConnection,
            self).config_mode(
            config_command=config_command,
            pattern=pattern,
            skip_check=skip_check)

    def send_config_set(
            self,
            config_commands=None,
            exit_config_mode=True,
            **kwargs):
        """IOS-XR requires you not exit from configuration mode."""
        return super(
            CiscoXr,
            self).send_config_set(
            config_commands=config_commands,
            exit_config_mode=False,
            **kwargs)

    def commit(self, confirm=False, confirm_delay=None, comment='', label='',
               replace=False,
               delay_factor=1,
               max_timeout=30):
        """
        Commit the candidate configuration.

        default (no options):
            command_string = commit
        confirm and confirm_delay:
            command_string = commit confirmed <confirm_delay>
        label (which is a label name):
            command_string = commit label <label>
        comment:
            command_string = commit comment <comment>

        supported combinations
        label and confirm:
            command_string = commit label <label> confirmed <confirm_delay>
        label and comment:
            command_string = commit label <label> comment <comment>

        All other combinations will result in an exception.

        failed commit message:
        % Failed to commit one or more configuration items during a pseudo-atomic operation. All
        changes made have been reverted. Please issue 'show configuration failed [inheritance]'
        from this session to view the errors

        message XR shows if other commits occurred:
        One or more commits have occurred from other configuration sessions since this session
        started or since the last commit was made from this session. You can use the 'show
        configuration commit changes' command to browse the changes.

        Exit of configuration mode with pending changes will cause the changes to be discarded and
        an exception to be generated.
        """
        delay_factor = self.select_delay_factor(delay_factor)
        if confirm and not confirm_delay:
            raise ValueError("Invalid arguments supplied to XR commit")
        if confirm_delay and not confirm:
            raise ValueError("Invalid arguments supplied to XR commit")
        if comment and confirm:
            raise ValueError("Invalid arguments supplied to XR commit")

        # wrap the comment in quotes
        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = '"{0}"'.format(comment)

        label = str(label)
        error_marker = 'Failed to'
        alt_error_marker = 'One or more commits have occurred from other'

        commit_str = 'commit '
        if replace:
            commit_str += 'replace '
        # Select proper command string based on arguments provided
        if label:
            if comment:
                command_string = 'label {0} comment {1}'.format(label, comment)
            elif confirm:
                command_string = 'label {0} confirmed {1}'.format(
                    label, str(confirm_delay))
            else:
                command_string = 'label {0}commit_str + '.format(label)
        elif confirm:
            command_string = 'confirmed {0}commit_str + '.format(
                str(confirm_delay))
        elif comment:
            command_string = 'comment {0}commit_str + '.format(comment)
        else:
            command_string = ''

        command_string = commit_str + command_string

        # Enter config mode (if necessary)
        # output = self.config_mode()
        output = ''
        output += self.send_command_expect(command_string,
                                           strip_prompt=False,
                                           strip_command=False,
                                           delay_factor=delay_factor,
                                           max_timeout=max_timeout)
        if error_marker in output:
            raise ValueError(
                "Commit failed with the following errors:\n\n{0}".format(output))
        if alt_error_marker in output:
            # Other commits occurred, don't proceed with commit
            output += self.send_command_timing("no",
                                               strip_prompt=False,
                                               strip_command=False,
                                               delay_factor=delay_factor,
                                               max_timeout=max_timeout)
            raise ValueError(
                "Commit failed with the following errors:\n\n{0}".format(output))

        return output

    def exit_config_mode(self, exit_config='end', 
                         skip_check=False, prompt_response="no"):
        """Exit configuration mode.
        When config/commit fails, exit may ask for commit the config 
        Say 'no' to handle the config failure
        """
        output = ''
        if skip_check or self.check_config_mode():
            output = self.send_command_expect(
                exit_config,
                strip_prompt=False,
                strip_command=False,
                auto_find_prompt=False,
                expect_string=self.current_prompt)
            if "Uncommitted changes found" in output:
                output = self.send_command_expect(
                    prompt_response,
                    strip_prompt=False,
                    strip_command=False,
                    auto_find_prompt=False,
                    expect_string=self.current_prompt)
            if skip_check:
                return output
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n','\r\r\n', '\n\r', or '\r' to '\n."""
        newline = re.compile(r'(\r\r\n|\r\n|\n\r|\r)')
        return newline.sub('\n', a_string)


class CiscoXrSSH(CiscoXr):
    '''
    CiscoXrSSH is based of CiscoXr -- CiscoBaseConnection
    '''
    pass


class CiscoXrTelnet(CiscoXr):
    '''
    CiscoXrTelnet is based of CiscoXr -- CiscoBaseConnection
    '''

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        if 'RP Node is not ' in self.find_prompt():
            # Incase of standby - skip rest of section
            return
        self.disable_paging(verbose=True)
        self.set_terminal_width(command='terminal width 511', verbose=True)

    def set_base_prompt(self, pri_prompt_terminator='#',
                        alt_prompt_terminator='>', delay_factor=1,
                        standby_prompt='RP Node is not ',
                        ):
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Cisco
        devices this will be set to router hostname (i.e. prompt without '>' or '#').

        This will be set on entering user exec or privileged exec on Cisco, but not when
        entering/exiting config mode.
        """
        prompt = self.find_prompt(delay_factor=delay_factor)
        list_of_valid_prompts = []
        list_of_valid_prompts.append(pri_prompt_terminator)
        list_of_valid_prompts.append(alt_prompt_terminator)
        if standby_prompt in prompt:
            self.base_prompt = prompt
            return self.base_prompt
        if not prompt[-1] in list_of_valid_prompts:
            raise ValueError("Router prompt not found: {0}".format(prompt))
        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]
        return self.base_prompt
