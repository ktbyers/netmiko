from netmiko.cisco_base_connection import CiscoSSHConnection


class LancomLCOSSX5SSH(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        The connection will enter `Privileged EXEC` by default, as the `EXEC` mode
        offers inconsistent command options
        """
        self._test_channel_read()
        super().send_command_timing(
            "enable",
            strip_prompt=False,
            strip_command=False,
        )
        super().set_base_prompt()
        super().disable_paging()
        self.clear_buffer()

    def set_terminal_width(self, *args, **kwargs) -> str:
        """
        LCOS SX 5 does not support 'terminal width', therefore skip it.
        """
        return ""

    def check_config_mode(
        self,
        check_string: str = "(Config)#",
        pattern: str = "#",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        :param check_string: Identification of configuration mode from the device
        :type check_string: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str

        :param force_regex: Use regular expression pattern to find check_string in output
        :type force_regex: bool

        :return: True if in configuration mode, False if not
        """
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def exit_enable_mode(self, exit_command: str = "end") -> str:
        """Exits enable (privileged exec) mode."""
        return super().exit_enable_mode(exit_command=exit_command)

    def cleanup(self, command: str = "logout") -> None:
        """
        Cleanup / Gracefully exit the SSH session

        :param command: LANCOM LCOS SX 5.x uses logout to exit the session
        :type command: str
        """
        # LANCOM does not allow running "Exec" commands in configuration mode
        if self.check_config_mode():
            command = "do " + command
        return super().cleanup(command)

    def save_config(
        self,
        cmd: str = "write memory confirm",
        confirm: bool = False,
        confirm_response: str = "y",
    ) -> str:
        """
        Save the running Config.

        :param cmd: The command to send to the device to save the configuration
        :type cmd: str

        :param confirm: Whether to confirm the save or not
        :type confirm: bool

        :param confirm_response: The response to send to the device to confirm the save
        :type confirm_response: str

        :param output_pattern: The pattern to match the output of the save command
        :type output_pattern: str
        """

        # LANCOM does not allow running "Exec" commands in configuration mode
        if self.check_config_mode():
            cmd = "do " + cmd
        return super().save_config(
            cmd=cmd,
            confirm=confirm,
            confirm_response=confirm_response,
        )
