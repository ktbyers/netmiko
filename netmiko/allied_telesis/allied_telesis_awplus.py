from netmiko.cisco_base_connection import CiscoBaseConnection
import time


class AlliedTelesisAwplusBase(CiscoBaseConnection):
    """Implement methods for interacting with Allied Telesis devices."""

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        """ AWPlus Configuration """

        self.disable_paging()
        self.set_base_prompt()
        time.sleep(0.3 * self.global_delay_factor)

    def _enter_shell(self) -> str:
        """Enter the Bourne Shell."""
        return self._send_command_str("start shell sh", expect_string=r"[\$#]")

    def _return_cli(self) -> str:
        """Return to the Awplus CLI."""
        return self._send_command_str("exit", expect_string=r"[#>]")

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "") -> str:
        """Exit configuration mode."""
        output = ""
        if self.check_config_mode():
            output += self._send_command_timing_str(
                exit_config, strip_prompt=False, strip_command=False
            )
            if "Exit with uncommitted changes?" in output:
                output += self._send_command_timing_str(
                    "yes", strip_prompt=False, strip_command=False
                )
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output


class AlliedTelesisAwplusSSH(AlliedTelesisAwplusBase):
    pass
