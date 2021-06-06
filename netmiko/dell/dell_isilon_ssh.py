import time
import re

from netmiko.base_connection import BaseConnection


class DellIsilonSSH(BaseConnection):
    def set_base_prompt(
        self, pri_prompt_terminator="$", alt_prompt_terminator="#", delay_factor=1
    ):
        """Determine base prompt."""
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )

    def strip_ansi_escape_codes(self, string_buffer):
        """Remove Null code"""
        output = re.sub(r"\x00", "", string_buffer)
        return super().strip_ansi_escape_codes(output)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self.zsh_mode()
        self.find_prompt(delay_factor=1)
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def zsh_mode(self, delay_factor=1, prompt_terminator="$"):
        """Run zsh command to unify the environment"""
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        command = self.RETURN + "zsh" + self.RETURN
        self.write_channel(command)
        time.sleep(1 * delay_factor)
        self.set_prompt()
        self.clear_buffer()

    def set_prompt(self, prompt_terminator="$"):
        prompt = f"PROMPT='%m{prompt_terminator}'"
        command = self.RETURN + prompt + self.RETURN
        self.write_channel(command)

    def disable_paging(self, *args, **kwargs):
        """Isilon doesn't have paging by default."""
        pass

    def check_enable_mode(self, check_string: str = r"\#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self, cmd: str = "sudo su", pattern: str ="ssword", enable_pattern=None, re_flags: int =re.IGNORECASE
    ) -> str:
        # FIX: might be able to just use the parent class
        delay_factor = self.select_delay_factor(delay_factor=1)
        output = ""
        if not self.check_enable_mode():
            output += self.send_command_timing(
                config_command, strip_prompt=False, strip_command=False
            )
            if "ssword:" in output:
                output = self.write_channel(self.normalize_cmd(self.secret))
            output += self.read_until_pattern(pattern=r"#.*$")
            time.sleep(1 * delay_factor)
            self.set_prompt(prompt_terminator="#")
            if not self.check_enable_mode():
                raise ValueError("Failed to enter enable mode")
        return output

    def exit_enable_mode(self, exit_command: str = "exit") -> str:
        return super().exit_enable_mode(exit_config=exit_config)

    def check_config_mode(self, check_string: str=r"\#", pattern: str="") -> str:
        """Use equivalent enable method."""
        return self.check_enable_mode(check_string=check_string)

    def config_mode(
        self,
        config_command: str = "sudo su",
        pattern: str = "ssword",
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Use equivalent enable method."""
        return self.enable(cmd=config_command, pattern=pattern, re_flags=re_flags)

    def exit_config_mode(self, exit_config="exit"):
        """Use equivalent enable method."""
        return self.exit_enable_mode(exit_command=exit_config)
