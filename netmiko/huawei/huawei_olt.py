import time
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.huawei import HuaweiTelnet


class HuaweiOLTTelnet(CiscoBaseConnection):
    telnet_login = HuaweiTelnet.telnet_login

    def disable_paging(self, command="scroll"):
        return super().disable_paging(command=command)

    def config_mode(self, config_command="config"):
        """Enter configuration mode."""
        self.enable()
        return super().config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config="return", pattern="#"):
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.send_command(command_string="undo interactive")
        self.send_command(command_string="undo smart")
        self.disable_paging(command="scroll")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def cleanup(self, command="undo scroll"):
        """Return paging before disconnect"""
        return super().cleanup(command=command)


class HuaweiOLTSSH(HuaweiOLTTelnet):
    pass
