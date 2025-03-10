from typing import Optional, Any, Union, Sequence, Iterator, TextIO
import re
import warnings
import time

from netmiko.no_enable import NoEnable
from netmiko.base_connection import DELAY_FACTOR_DEPR_SIMPLE_MSG
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.exceptions import NetmikoAuthenticationException
from netmiko import log


class HuaweiBase(NoEnable, CiscoBaseConnection):
    prompt_pattern = r"[\]>]"
    password_change_prompt = r"(?:Change now|Please choose)"
    prompt_or_password_change = rf"(?:Change now|Please choose|{prompt_pattern})"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        # The _test_channel_read happens in special_login_handler()
        self.set_base_prompt()
        self.disable_paging(command="screen-length 0 temporary")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def strip_ansi_escape_codes(self, string_buffer: str) -> str:
        """
        Huawei does a strange thing where they add a space and then add ESC[1D
        to move the cursor to the left one.

        The extra space is problematic.
        """
        code_cursor_left = chr(27) + r"\[\d+D"
        output = string_buffer
        pattern = rf" {code_cursor_left}"
        output = re.sub(pattern, "", output)

        return super().strip_ansi_escape_codes(output)

    def config_mode(
        self,
        config_command: str = "system-view",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "return", pattern: str = r">") -> str:
        """Exit configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_config_mode(
        self, check_string: str = "]", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Checks whether in configuration mode. Returns a boolean."""
        return super().check_config_mode(check_string=check_string)

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "]",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts.
        For Huawei this will be the router prompt with < > or [ ] stripped off.

        This will be set on logging in, but not when entering system-view
        """

        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

        # Strip off any leading HRP_. characters for USGv5 HA
        prompt = re.sub(r"^HRP_.", "", prompt, flags=re.M)

        # Strip off leading terminator
        prompt = prompt[1:]
        prompt = prompt.strip()
        self.base_prompt = prompt
        log.debug(f"prompt: {self.base_prompt}")
        return self.base_prompt

    def save_config(
        self, cmd: str = "save", confirm: bool = True, confirm_response: str = "y"
    ) -> str:
        """Save Config for HuaweiSSH

        Expected behavior:

        ######################################################################
        Warning: The current configuration will be written to the device.
        Are you sure to continue?[Y/N]:y
         It will take several minutes to save configuration file, please wait.....................
         Configuration file had been saved successfully
         Note: The configuration file will take effect after being activated
        ######################################################################
        or
        ######################################################################
        Warning: The current configuration will be written to the device. Continue? [Y/N]:y
        Now saving the current configuration to the slot 1 .
        Info: Save the configuration successfully.
        ######################################################################
        """

        # Huawei devices might break if you try to use send_command_timing() so use send_command()
        # instead.
        if confirm:
            pattern = rf"(?:[Cc]ontinue\?|{self.prompt_pattern})"
            output = self._send_command_str(
                command_string=cmd,
                expect_string=pattern,
                strip_prompt=False,
                strip_command=False,
                read_timeout=100.0,
            )
            if confirm_response and re.search(r"[Cc]ontinue\?", output):
                output += self._send_command_str(
                    command_string=confirm_response,
                    expect_string=self.prompt_pattern,
                    strip_prompt=False,
                    strip_command=False,
                    read_timeout=100.0,
                )
        # no confirm.
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self._send_command_str(
                command_string=cmd,
                strip_prompt=False,
                strip_command=False,
                read_timeout=100.0,
            )
        return output

    def cleanup(self, command: str = "quit") -> None:
        return super().cleanup(command=command)


class HuaweiSSH(HuaweiBase):
    """Huawei SSH driver."""

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        # Huawei prompts for password change before displaying the initial base prompt.
        # Search for that password change prompt or for base prompt.
        data = self.read_until_pattern(pattern=self.prompt_or_password_change)
        if re.search(self.password_change_prompt, data):
            self.write_channel("N" + self.RETURN)
            self.read_until_pattern(pattern=self.prompt_pattern)

        # Huawei prompts for secure the configuration before displaying the initial base prompt.
        if re.search(
            r"security\srisks\sin\sthe\sconfiguration\sfile.*\[y\/n\]", data, flags=re.I
        ):
            self.send_command("Y", expect_string=r"(?i)continue.*\[y\/n\]")
            self.send_command(
                "Y", expect_string=r"saved\ssuccessfully", read_timeout=60
            )
            self.read_until_pattern(pattern=self.prompt_pattern)


class HuaweiTelnet(HuaweiBase):
    """Huawei Telnet driver."""

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"",
        alt_prompt_terminator: str = r"",
        username_pattern: str = r"(?:user:|username|login|user name)",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        """Telnet login for Huawei Devices"""
        output = ""
        return_msg = ""
        try:
            # Search for username pattern / send username
            output = self.read_until_pattern(pattern=username_pattern, re_flags=re.I)
            return_msg += output
            self.write_channel(self.username + self.TELNET_RETURN)

            # Search for password pattern / send password
            output = self.read_until_pattern(pattern=pwd_pattern, re_flags=re.I)
            return_msg += output
            assert self.password is not None
            self.write_channel(self.password + self.TELNET_RETURN)

            # Waiting for the prompt or password change message
            output = self.read_until_pattern(pattern=self.prompt_or_password_change)
            return_msg += output

            # If password change prompt, send "N"
            if re.search(self.password_change_prompt, output):
                self.write_channel("N" + self.TELNET_RETURN)
                output = self.read_until_pattern(pattern=self.prompt_pattern)
                return_msg += output
                return return_msg
            elif re.search(self.prompt_pattern, output):
                return return_msg

            # Should never be here
            raise EOFError

        except EOFError:
            assert self.remote_conn is not None
            self.remote_conn.close()
            msg = f"Login failed: {self.host}"
            raise NetmikoAuthenticationException(msg)


class HuaweiVrpv8SSH(HuaweiSSH):
    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """Huawei VRPv8 requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def commit(
        self,
        comment: str = "",
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
    ) -> str:
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        default:
           command_string = commit
        comment:
           command_string = commit comment <comment>

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.
        """

        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        error_marker = "Failed to generate committed config"
        command_string = "commit"

        if comment:
            command_string += f' comment "{comment}"'

        output = self.config_mode()
        output += self._send_command_str(
            command_string,
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
            expect_string=r"]",
        )
        output += self.exit_config_mode()

        if error_marker in output:
            raise ValueError(f"Commit failed with following errors:\n\n{output}")
        return output
