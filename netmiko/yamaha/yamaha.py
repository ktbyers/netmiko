import time
import re
from netmiko.base_connection import BaseConnection


class YamahaBase(BaseConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging(command="console lines infinity")
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "administrator",
        pattern: str = r"Password",
        re_flags: int = re.IGNORECASE,
    ) -> str:
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        """
        When any changes have been made, the prompt 'Save new configuration ? (Y/N)'
        appears before exiting. Ignore this by entering 'N'.
        """
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            time.sleep(1)
            output = self.read_channel()
            if "(Y/N)" in output:
                self.write_channel("N")
            output += self.read_until_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def check_config_mode(self, check_string: str = "#", pattern: str = "") -> bool:
        """Checks if the device is in administrator mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "administrator",
        pattern: str = "ssword",
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter into administrator mode and configure device."""
        return self.enable()

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = ">") -> str:
        """
        No action taken. Call 'exit_enable_mode()' to explicitly exit Administration
        Level.
        """
        return ""

    def save_config(
        self, cmd: str = "save", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Saves Config."""
        if confirm is True:
            raise ValueError("Yamaha does not support save_config confirmation.")
        self.enable()
        # Some devices are slow so match on trailing-prompt if you can
        output = self.send_command(command_string=cmd)
        assert isinstance(output, str)
        return output


class YamahaSSH(YamahaBase):
    """Yamaha SSH driver."""

    pass


class YamahaTelnet(YamahaBase):
    """Yamaha Telnet driver."""

    pass
