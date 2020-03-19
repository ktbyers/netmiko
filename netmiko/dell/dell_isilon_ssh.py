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

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Isilon."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on Isilon."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Isilon."""
        pass

    def check_config_mode(self, check_string="#"):
        return super().check_config_mode(check_string=check_string)

    def config_mode(self, config_command="sudo su"):
        """Attempt to become root."""
        delay_factor = self.select_delay_factor(delay_factor=1)
        output = ""
        if not self.check_config_mode():
            output += self.send_command_timing(
                config_command, strip_prompt=False, strip_command=False
            )
            if "Password:" in output:
                output = self.write_channel(self.normalize_cmd(self.secret))
            self.set_prompt(prompt_terminator="#")
            time.sleep(1 * delay_factor)
            self.set_base_prompt()
            if not self.check_config_mode():
                raise ValueError("Failed to configuration mode")
        return output

    def exit_config_mode(self, exit_config="exit"):
        """Exit enable mode."""
        return super().exit_config_mode(exit_config=exit_config)
