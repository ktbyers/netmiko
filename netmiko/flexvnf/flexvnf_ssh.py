from typing import Optional, Any
import re
import time
import warnings

from netmiko.no_enable import NoEnable
from netmiko.base_connection import BaseConnection, DELAY_FACTOR_DEPR_SIMPLE_MSG


class FlexvnfSSH(NoEnable, BaseConnection):
    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        self._test_channel_read(pattern=r"[\$@>%]")
        self.enter_cli_mode()
        self.set_base_prompt()
        self.set_terminal_width(command="set screen width 511", pattern="set")
        self.disable_paging(command="set screen length 0")

    def enter_cli_mode(self) -> None:
        """Check if at shell prompt root@ and go into CLI."""
        delay_factor = self.select_delay_factor(delay_factor=0)
        count = 0
        cur_prompt = ""
        while count < 50:
            self.write_channel(self.RETURN)
            time.sleep(0.1 * delay_factor)
            cur_prompt = self.read_channel()
            if re.search(r"admin@", cur_prompt) or re.search(
                r"\$$", cur_prompt.strip()
            ):
                self.write_channel("cli" + self.RETURN)
                time.sleep(0.3 * delay_factor)
                self.clear_buffer()
                break
            elif ">" in cur_prompt or "%" in cur_prompt:
                break
            count += 1

    def check_config_mode(
        self, check_string: str = "]", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string)

    def config_mode(
        self, config_command: str = "configure", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(
        self, exit_config: str = "exit configuration-mode", pattern: str = ""
    ) -> str:
        """Exit configuration mode."""
        output = ""
        if self.check_config_mode():
            output += self._send_command_timing_str(
                exit_config, strip_prompt=False, strip_command=False
            )
            # if 'Exit with uncommitted changes?' in output:
            if "uncommitted changes" in output:
                output += self._send_command_timing_str(
                    "yes", strip_prompt=False, strip_command=False
                )
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def commit(
        self,
        confirm: bool = False,
        confirm_delay: Optional[int] = None,
        check: bool = False,
        comment: str = "",
        and_quit: bool = False,
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
    ) -> str:
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        default:
            command_string = commit
        check and (confirm or confirm_dely or comment):
            Exception
        confirm_delay and no confirm:
            Exception
        confirm:
            confirm_delay option
            comment option
            command_string = commit confirmed or commit confirmed <confirm_delay>
        check:
            command_string = commit check

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        """

        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        if check and (confirm or confirm_delay or comment):
            raise ValueError("Invalid arguments supplied with commit check")

        if confirm_delay and not confirm:
            raise ValueError(
                "Invalid arguments supplied to commit method both confirm and check"
            )

        # Select proper command string based on arguments provided
        command_string = "commit"
        commit_marker = "Commit complete."
        if check:
            command_string = "commit check"
            commit_marker = "Validation complete"
        elif confirm:
            if confirm_delay:
                command_string = "commit confirmed " + str(confirm_delay)
            else:
                command_string = "commit confirmed"
            commit_marker = "commit confirmed will be automatically rolled back in"

        # wrap the comment in quotes
        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = f'"{comment}"'
            command_string += " comment " + comment

        if and_quit:
            command_string += " and-quit"

        # Enter config mode (if necessary)
        output = self.config_mode()
        # and_quit will get out of config mode on commit
        if and_quit:
            prompt = self.base_prompt
            output += self._send_command_str(
                command_string,
                expect_string=prompt,
                strip_prompt=True,
                strip_command=True,
                read_timeout=read_timeout,
            )
        else:
            output += self._send_command_str(
                command_string,
                strip_prompt=True,
                strip_command=True,
                read_timeout=read_timeout,
            )

        if commit_marker not in output:
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")

        return output

    def strip_prompt(self, *args: Any, **kwargs: Any) -> str:
        """Strip the trailing router prompt from the output."""
        a_string = super().strip_prompt(*args, **kwargs)
        return self._strip_context_items(a_string)

    def _strip_context_items(self, a_string: str) -> str:
        """Strip FLEXVNF-specific output.

        FLEXVNF will also put a configuration context:
        [edit]

        and various chassis contexts:
        {master:0}, {backup:1}

        This method removes those lines.
        """
        strings_to_strip = [
            r"admin@lab-pg-dev-cp02v.*",
            r"\[edit.*\]",
            r"\[edit\]",
            r"\[ok\]",
            r"\[.*\]",
            r"\{master:.*\}",
            r"\{backup:.*\}",
            r"\{line.*\}",
            r"\{primary.*\}",
            r"\{secondary.*\}",
        ]

        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[0]

        for pattern in strings_to_strip:
            if re.search(pattern, last_line):
                return self.RESPONSE_RETURN.join(response_list[:-1])
        return a_string
