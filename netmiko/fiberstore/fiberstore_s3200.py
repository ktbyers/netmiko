"""Fiberstore S3200 Driver."""
from __future__ import unicode_literals
from paramiko import SSHClient
import time
from os import path
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import NetmikoAuthenticationException


class SSHClient_noauth(SSHClient):
    def _auth(self, username, *args):
        self._transport.auth_none(username)
        return


class FiberStoreConnectSSH(CiscoSSHConnection):
    """Fiberstore S3200 Driver.
    To make it work, we have to override the SSHClient _auth method.
    If we use login/password, the ssh server use the (none) auth mechanism.
    """
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        output = self._test_channel_read()
        if "% Authentication Failed" in output:
            self.remote_conn.close()
            msg = f"Login failed: {self.host}"
            raise NetmikoAuthenticationException(msg)

        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, pri_prompt_terminator='>', alt_prompt_terminator='#',
                        delay_factor=1):
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        prompt = super(FiberStoreConnectSSH, self).set_base_prompt(
                                                      pri_prompt_terminator=pri_prompt_terminator,
                                                      alt_prompt_terminator=alt_prompt_terminator,
                                                      delay_factor=delay_factor)
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def enable(self):
         """there is no enable mode"""
         return 
    def check_config_mode(self, check_string='(config)#'):
        """Checks if the device is in configuration mode"""
        return super(FiberStoreConnectSSH, self).check_config_mode(check_string=check_string)

    def config_mode(self, config_command='config'):
        """Enter configuration mode."""
        return super(FiberStoreConnectSSH, self).config_mode(config_command=config_command)

    def save_config(self):
        """Save Config on Fiberstore S3200"""
        return self.send_command('copy running-config startup-config')


    def _build_ssh_client(self):
        """Prepare for Paramiko SSH connection.
        See base_connection.py file for any updates.
        """
        # Create instance of SSHClient object
        # If user does not provide SSH key, we use noauth
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

    def special_login_handler(self, delay_factor=1):
        """
        Fiberstore S3200 presents with the following on login
        Username:
        Password: ****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * .5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if 'Username:' in output:
                    self.write_channel(self.username + self.RETURN)
                elif 'Password:' in output:
                    self.write_channel(self.password + self.RETURN)
                    return
            time.sleep(delay_factor)
            i += 1
