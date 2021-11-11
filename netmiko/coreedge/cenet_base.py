from netmiko.cisco_base_connection import CiscoSSHConnection


class CenetBase(CiscoSSHConnection):
    def check_config_mode(self, check_string=")#", pattern=r"[>\#]"):

        """
        Checks if the device is in configuration mode or not.
        CENOS uses "<hostname>(config)#" as config prompt
        """

        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=pattern)
        return check_string in output

    def save_config(
        self,
        cmd: str = "write",
        confirm: bool = True,
        confirm_response: str = "Yes",
    ) -> str:

        """Save config: write"""
        if confirm:
            output = self.send_command_timing(
                command_string=cmd,
                strip_prompt=False,
                strip_command=False,
            )
            if confirm_response:
                output += self.send_command_timing(
                    command_string=confirm_response,
                    strip_prompt=False,
                    strip_command=False,
                )
                self.send_command(
                    self.RETURN,
                    strip_prompt=False,
                    strip_command=False,
                    expect_string=r"#",
                )
            else:
                # Send enter by default
                output += self.send_command_timing(
                    self.RETURN,
                    strip_prompt=False,
                    strip_command=False,
                )
        else:
            output = self.send_command(
                command_string=cmd,
                strip_prompt=False,
                strip_command=False,
            )
        return output
