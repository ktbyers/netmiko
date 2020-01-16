"""Dell PowerConnect Driver."""
from paramiko import SSHClient
import time
from os import path
from netmiko.cisco_base_connection import CiscoBaseConnection


class SSHClient_noauth(SSHClient):
    def _auth(self, username, *args):
        self._transport.auth_none(username)
        return


class DellPowerConnectBase(CiscoBaseConnection):
    """Dell PowerConnect Driver."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="terminal datadump")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(
        self, pri_prompt_terminator=">", alt_prompt_terminator="#", delay_factor=1
    ):
        """Sets self.base_prompt: used as delimiter for stripping of trailing prompt in output."""
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def check_config_mode(self, check_string="(config)#"):
        """Checks if the device is in configuration mode"""
        return super().check_config_mode(check_string=check_string)

    def config_mode(self, config_command="config"):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command)


class DellPowerConnectSSH(DellPowerConnectBase):
    """Dell PowerConnect Driver.

    To make it work, we have to override the SSHClient _auth method.
    If we use login/password, the ssh server use the (none) auth mechanism.
    """

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
        Powerconnect presents with the following on login

        User Name:

        Password: ****
        """
        delay_factor = self.select_delay_factor(delay_factor)
        i = 0
        time.sleep(delay_factor * 0.5)
        output = ""
        while i <= 12:
            output = self.read_channel()
            if output:
                if "User Name:" in output:
                    self.write_channel(self.username + self.RETURN)
                elif "Password:" in output:
                    self.write_channel(self.password + self.RETURN)
                    break
                time.sleep(delay_factor * 1)
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 1.5)
            i += 1


class DellPowerConnectTelnet(DellPowerConnectBase):
    """Dell PowerConnect Telnet Driver."""

    pass
