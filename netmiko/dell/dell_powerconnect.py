"""Dell PowerConnect Driver."""
import time
from netmiko.channel import SSHChannel
from netmiko.cisco_base_connection import CiscoBaseConnection


class DellPowerConnectChannel(SSHChannel):
    def _build_ssh_client(self, no_auth=True):
        """Allow passwordless authentication for HP devices being provisioned."""
        if not self.use_keys:
            super._build_ssh_client(no_auth=no_auth)
        else:
            super._build_ssh_client(no_auth=False)


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

    def _open(self, channel_class=DellPowerConnectChannel):
        """Override channel object creation."""

        super()._open(channel_class=channel_class)

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
