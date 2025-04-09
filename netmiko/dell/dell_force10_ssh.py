"""Dell Force10 Driver - supports DNOS9."""

import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class DellForce10SSH(CiscoSSHConnection):
    """Dell Force10 Driver - supports DNOS9."""

    prompt_pattern = r"[>#]"

    def session_preparation(self) -> None:
        """Check if we have a prompt and acknowledge if we do."""

        data = self.read_until_pattern(pattern=f"y/n|{self.prompt_pattern}")
        # If "banner login acknowledge enable" is set, it will require you to
        # press 'y' to accept the banner before you login. This will accept
        # if it occurs
        # Line looks like:
        # Have you read and do you acknowledge the above statement? [y/n]: y
        # switch>
        #
        if re.search(r"y\/n", data):
            self.write_channel(f"y{self.RETURN}")

        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = prompt_pattern,
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.
        """
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
