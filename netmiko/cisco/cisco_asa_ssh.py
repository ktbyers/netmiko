"""Subclass specific to Cisco ASA."""

from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection, CiscoFileTransfer


class CiscoAsaSSH(CiscoSSHConnection):
    """Subclass specific to Cisco ASA."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        if self.secret:
            self.enable()
        else:
            self.asa_login()
        self.disable_paging(command="terminal pager 0")
        self.set_terminal_width(command="terminal width 511")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def send_command_timing(self, *args, **kwargs):
        """
        If the ASA is in multi-context mode, then the base_prompt needs to be
        updated after each context change.
        """
        output = super(CiscoAsaSSH, self).send_command_timing(*args, **kwargs)
        if len(args) >= 1:
            command_string = args[0]
        else:
            command_string = kwargs['command_string']
        if "changeto" in command_string:
            self.set_base_prompt()
        return output

    def send_command(self, *args, **kwargs):
        """
        If the ASA is in multi-context mode, then the base_prompt needs to be
        updated after each context change.
        """
        if len(args) >= 1:
            command_string = args[0]
        else:
            command_string = kwargs['command_string']

        # If changeto in command, look for '#' to determine command is done
        if "changeto" in command_string:
            if len(args) <= 1:
                expect_string = kwargs.get('expect_string', '#')
                kwargs['expect_string'] = expect_string
        output = super(CiscoAsaSSH, self).send_command(*args, **kwargs)

        if "changeto" in command_string:
            self.set_base_prompt()

        return output

    def send_command_expect(self, *args, **kwargs):
        """Backwards compaitibility."""
        return self.send_command(*args, **kwargs)

    def set_base_prompt(self, *args, **kwargs):
        """
        Cisco ASA in multi-context mode needs to have the base prompt updated
        (if you switch contexts i.e. 'changeto')

        This switch of ASA contexts can occur in configuration mode. If this
        happens the trailing '(config*' needs stripped off.
        """
        cur_base_prompt = super(CiscoAsaSSH, self).set_base_prompt(*args, **kwargs)
        match = re.search(r'(.*)\(conf.*', cur_base_prompt)
        if match:
            # strip off (conf.* from base_prompt
            self.base_prompt = match.group(1)
            return self.base_prompt

    def asa_login(self):
        """
        Handle ASA reaching privilege level 15 using login

        twb-dc-fw1> login
        Username: admin
        Password: ************
        """
        delay_factor = self.select_delay_factor(0)

        i = 1
        max_attempts = 50
        self.write_channel("login" + self.RETURN)
        while i <= max_attempts:
            time.sleep(.5 * delay_factor)
            output = self.read_channel()
            if 'sername' in output:
                self.write_channel(self.username + self.RETURN)
            elif 'ssword' in output:
                self.write_channel(self.password + self.RETURN)
            elif '#' in output:
                break
            else:
                self.write_channel("login" + self.RETURN)
            i += 1

    def save_config(self, cmd='write mem', confirm=False):
        """Saves Config"""
        return super(CiscoAsaSSH, self).save_config(cmd=cmd, confirm=confirm)

    def set_terminal_width(self, command="", delay_factor=1):
        """
        On ASAs, terminal width is set in global configuration mode. First,
        we should check to see if we can access config mode. If we can't,
        then don't do anything. If we can and the current terminal width
        is not already 511, store the current terminal width as an attribute
        of this object so that it can be restored when our session is complete.
        """
        if not super(CiscoAsaSSH, self).check_config_mode():
            try:
                super(CiscoAsaSSH, self).config_mode()
            except ValueError:
                # Unable to access global config mode
                return None
        if not hasattr(self, "prev_term_width"):
            output = self.send_command("show run | i terminal width")
            if output:
                if not "511" in output.split()[-1]:
                    self.prev_term_width = output.split()[-1]
            else:
                self.prev_term_width = 80
        super(CiscoAsaSSH, self).set_terminal_width(command=command)
        super(CiscoAsaSSH, self).exit_config_mode()
    
    def cleanup(self):
        """
        Gracefully exit the SSH session. On ASAs, we need to try to restore
        the user-configured terminal width before exiting the session.
        """
        try:
            self.set_terminal_width(command="terminal width {}".format(self.prev_term_width))
        except AttributeError:
            pass
        super(CiscoAsaSSH, self).cleanup()

class CiscoAsaFileTransfer(CiscoFileTransfer):
    """Cisco ASA SCP File Transfer driver."""
    pass
