import time
from typing import Optional

from netmiko.cisco_base_connection import CiscoSSHConnection


class AlaxalaAx36sBase(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        time.sleep(0.3 * self.global_delay_factor)
        self.disable_paging(command="set terminal pager disable")

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        base_prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        self.base_prompt = base_prompt[1:]
        return self.base_prompt

    def exit_config_mode(self, exit_command: str = "end", pattern: str = "") -> str:
        """
        If there are unsaved configuration changes, the prompt is
        "Unsaved changes found! Do you exit "configure" without save ? (y/n):" is output.
        enter "y" to exit configure mode.
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            time.sleep(1)
            output = self.read_channel()
            if "(y/n)" in output:
                self.write_channel("y\n")
            if self.base_prompt not in output:
                output += self.read_until_prompt(read_entire_line=True)
            if self.check_config_mode():
                raise ValueError("Failed to exit config mode.")
        return output

    def save_config(
        self,
        cmd: str = "write",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """
        "save_config" must be executed in config mode.
        if the configuration change is not saved,
        a "!" will appear at the beginning of the prompt.
        """
        output = ""
        if not self.check_config_mode():
            self.config_mode()
        output = self._send_command_timing_str(
            command_string=cmd, strip_prompt=False, strip_command=False
        )
        output += self._send_command_timing_str(
            self.RETURN, strip_prompt=False, strip_command=False
        )
        self.exit_config_mode()
        if self.base_prompt not in output:
            output += self.read_until_prompt(read_entire_line=True)
        return output


class AlaxalaAx36sSSH(AlaxalaAx36sBase):
    """AlaxalA AX36S SSH driver."""

    pass
