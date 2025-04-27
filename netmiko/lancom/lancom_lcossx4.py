from netmiko.cisco_base_connection import CiscoSSHConnection


class LancomLCOSSX4SSH(CiscoSSHConnection):
    promt_pattern = r"[#$]"

    def check_config_mode(
        self,
        check_string: str = "(config)#",
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

    def cleanup(self, command: str = "logout") -> None:
        """
        Cleanup / Gracefully exit the SSH session

        :param command: LANCOM LCOS SX 4.x uses logout to exit the session
        :type command: str
        """
        if self.check_config_mode():
            command = "do " + command
        return super().cleanup(command)

    def save_config(
        self,
        cmd: str = "copy running-config startup-config",
        confirm: bool = False,
        confirm_response: str = "",
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
        return self._send_command_str(cmd)
