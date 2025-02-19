import re
from typing import Optional
from netmiko.exceptions import NetmikoTimeoutException
from netmiko.huawei.huawei import HuaweiBase, HuaweiTelnet


class OptilinkGOLT944Base(HuaweiBase):
    """Optilink GOLT 944"""

    pass


class OptilinkGOLT944Telnet(HuaweiTelnet):
    """Optilink GOLT 944 telnet driver"""

    def check_enable_mode(self, check_string: str = "<") -> bool:
        """Check if in enable mode. Return a boolean."""
        self.write_channel(self.RETURN)
        output = self.read_until_prompt(read_entire_line=True)
        return check_string in output

    def check_config_mode(
        self, check_string: str = "]", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Check if the device is in configuration mode or not."""
        self.write_channel(self.RETURN)
        if not pattern:
            output = self.read_channel_timing(read_timeout=10.0)
        else:
            output = self.read_until_pattern(pattern=pattern)

        if force_regex:
            return bool(re.search(check_string, output))
        else:
            return check_string in output

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode."""
        output = ""
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )

        # Check if in enable mode already.
        if check_state and self.check_enable_mode():
            return output

        # Send "enable" mode command
        self.write_channel(self.normalize_cmd(cmd))
        try:
            # Read the command echo
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(pattern=re.escape(cmd.strip()))

            # Search for trailing prompt or password pattern
            output += self.read_until_prompt_or_pattern(
                pattern=pattern, re_flags=re_flags
            )

            # Send the "secret" in response to password pattern
            if re.search(pattern, output):
                self.write_channel(self.normalize_cmd(self.secret))
                output += self.read_until_prompt()

            # Search for terminating pattern if defined
            if enable_pattern and not re.search(enable_pattern, output):
                output += self.read_until_pattern(pattern=enable_pattern)
            elif not self.check_enable_mode():
                raise ValueError(msg)

        except NetmikoTimeoutException as e:
            raise ValueError(msg) from e

        return output

    def config_mode(
        self, config_command: str = "sys", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter into configuration mode."""
        output = ""
        if not self.check_config_mode():
            self.write_channel(self.normalize_cmd(config_command))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(config_command.strip())
                )
            if pattern:
                output += self.read_until_pattern(pattern=pattern, re_flags=re_flags)
            else:
                output += self.read_until_prompt(read_entire_line=True)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode.")
        return output

    def exit_enable_mode(self, exit_command: str = "quit") -> str:
        """Exit from enable mode."""
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            self.read_until_pattern(pattern=exit_command)
            # output += self.read_until_pattern(pattern=r">")
            output += self.read_until_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def exit_config_mode(self, exit_config: str = "quit", pattern: str = "") -> str:
        """Exit from configuration mode.
        :param exit_config: Command to exit configuration mode
        :type exit_config: str
        :param pattern: Pattern to terminate reading of channel
        :type pattern: str
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(exit_config.strip())
                )
            if pattern:
                output += self.read_until_pattern(pattern=pattern)
            else:
                output += self.read_until_prompt(read_entire_line=True)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>\]]")
        self.set_base_prompt()
        self.enable()
        self.config_mode()
        self.disable_paging(command="screen-rows per-page 0")
        self.exit_config_mode()
        self.exit_enable_mode()
