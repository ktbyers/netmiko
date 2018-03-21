"""Calix B6 SSH Driver for Netmiko"""
from __future__ import unicode_literals

import time
from os import path

from paramiko import SSHClient

from netmiko.cisco_base_connection import CiscoSSHConnection


class SSHClient_noauth(SSHClient):
    """Set noauth when manually handling SSH authentication."""
    def _auth(self, username, *args):
        self._transport.auth_none(username)
        return


class CalixB6Base(CiscoSSHConnection):
    """Common methods for Calix B6, both SSH and Telnet."""
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get('default_enter')
        kwargs['default_enter'] = '\r\n' if default_enter is None else default_enter
        super(CalixB6SSH, self).__init__(*args, **kwargs)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command="terminal width 511")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def special_login_handler(self, delay_factor=1):
        """
        Calix B6 presents with the following on login:

        login as:
        Password: ****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * .25)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if 'login as:' in output:
                    self.write_channel(self.username + self.RETURN)
                elif 'Password:' in output:
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 0.5)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1)
            i += 1

    def check_config_mode(self, check_string=')#', pattern=''):
        """Checks if the device is in configuration mode"""
        return super(CalixB6Base, self).check_config_mode(
            check_string=check_string)

    def save_config(self, cmd='copy run start', confirm=False):
        return super(CalixB6Base, self).save_config(cmd=cmd, confirm=confirm)


class CalixB6SSH(CalixB6Base):
    """Calix B6 SSH Driver.

    To make it work, we have to override the SSHClient _auth method and manually handle
    the username/password.
    """
    def _build_ssh_client(self):
        """Prepare for Paramiko SSH connection."""
        # Create instance of SSHClient object
        # If not using SSH keys, we use noauth
        if not self.use_keys:
            remote_conn_pre = SSHClient_noauth()
        else:
            remote_conn_pre = SSHClient()

        # Load host_keys for better SSH security
        if self.system_host_keys:
            remote_conn_pre.load_system_host_keys()
        if self.alt_host_keys and path.isfile(self.alt_key_file):
            remote_conn_pre.load_host_keys(self.alt_key_file)

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        remote_conn_pre.set_missing_host_key_policy(self.key_policy)
        return remote_conn_pre


class CalixB6Telnet(CalixB6Base):
    """Calix B6 Telnet Driver."""
    pass
