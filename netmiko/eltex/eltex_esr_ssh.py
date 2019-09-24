import time
from netmiko.cisco_base_connection import CiscoSSHConnection


class EltexEsrSSH(CiscoSSHConnection):
    """Netmiko support for routers Eltex ESR."""

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="terminal datadump")

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def config_mode(self, config_command="configure", pattern=r")#"):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command, pattern=pattern)

    def check_config_mode(self, check_string="(config", pattern=""):
        """Checks whether in configuration mode. Returns a boolean."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(self, *args, **kwargs):
        """Not Implemented (use commit() method)"""
        raise NotImplementedError

    def commit(self, delay_factor=1):
        """
        Commit the candidate configuration.
        Commit the entered configuration.
        Raise an error and return the failure
        if the commit fails.
        default:
           command_string = commit
        """

        delay_factor = self.select_delay_factor(delay_factor)
        error_marker = "Can't commit configuration"
        command_string = "commit"

        if self.check_config_mode():
            self.exit_config_mode()

        output = self.send_command(
            command_string=command_string, delay_factor=delay_factor
        )

        if error_marker in output:
            raise ValueError(
                "Commit failed with following errors:\n\n{}".format(output)
            )
        return output

    def _confirm(self, delay_factor=1):
        """
        Confirm the candidate configuration.
        Raise an error and return the failure if the confirm fails.
        """

        delay_factor = self.select_delay_factor(delay_factor)
        error_marker = "Nothing to confirm in configuration"
        command_string = "confirm"

        if self.check_config_mode():
            self.exit_config_mode()

        output = self.send_command(
            command_string=command_string, delay_factor=delay_factor
        )

        if error_marker in output:
            raise ValueError(
                "Confirm failed with following errors:\n\n{}".format(output)
            )
        return output

    def _restore(self, delay_factor=1):
        """
        Restore the candidate configuration.

        Raise an error and return the failure if the restore fails.
        """

        delay_factor = self.select_delay_factor(delay_factor)
        error_marker = "Can't find backup of previous configuration!"
        command_string = "restore"

        if self.check_config_mode():
            self.exit_config_mode()

        output = self.send_command(
            command_string=command_string, delay_factor=delay_factor
        )

        if error_marker in output:
            raise ValueError(
                "Restore failed with following errors:\n\n{}".format(output)
            )
        return output
