"""A10 support."""

import re
from netmiko.cisco_base_connection import CiscoSSHConnection


class A10SSH(CiscoSSHConnection):
    """A10 support."""

    def session_preparation(self) -> None:
        """A10 requires to be enable mode to disable paging."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()

        # terminal width ill not do anything without A10 specific command
        # self.set_terminal_width()
        self.disable_paging(command="terminal length 0")

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = ")#", force_regex: bool = False
    ) -> bool:
        self.write_channel(self.RETURN)

        # You can encounter an issue here (on router name changes) prefer delay-based solution
        if not pattern:
            output = self.read_channel_timing(read_timeout=10.0)
        else:
            output = self.read_until_pattern(pattern=pattern)

        # A10 can do this 'LBR1_PROD-EXT_(NOLICENSE)#' when not licensed (e.g. gns3)
        # Example, config: LBR1_PROD-EXT_(config)(NOLICENSE)#
        # Example, outside of config LBR1_PROD-EXT_(NOLICENSE)#
        output = output.replace("(NOLICENSE)", "")

        if force_regex:
            return bool(re.search(check_string, output))
        else:
            return check_string in output

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Not Implemented"""
        raise NotImplementedError
