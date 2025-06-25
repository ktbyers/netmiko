from typing import Optional
import re
import time
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.exceptions import NetmikoTimeoutException, ReadTimeout


class KontronOSBase(CiscoBaseConnection):
    """Base class for Kontron OLT devices using Iskratel CLI Engine."""

    prompt_pattern = r"OLT[1-4]-[A-Z]{4}[0-2][0-9]>"
    config_mode_prompt_pattern = r"OLT[1-4]-[A-Z]{4}[0-2][0-9]\([^\)]*\)#"

    def __init__(self, *args, **kwargs):
        self.debug_mode = kwargs.pop('debug_mode', False)
        super().__init__(*args, **kwargs)

    def _debug_print(self, message: str) -> None:
        if self.debug_mode:
            print(message)

    def _strip_prompt_garbage(self, text: str) -> str:
        ansi_escape = re.compile(r'\x1b\[[0-9;]*[mGKHFABCDsuJ]|\x1b[78]|\x1b\].*?\x07')
        text = ansi_escape.sub('', text)
        text = text.replace('\x07', '').replace('\x08', '').replace('\r', '')
        return text.strip()

    def session_preparation(self) -> None:
        self.ansi_escape_codes = True
        self.read_channel()
        self.write_channel("\n")
        time.sleep(1)
        prompt_output = self.read_channel()
        cleaned_prompt = self._strip_prompt_garbage(prompt_output)

        if re.search(self.prompt_pattern, cleaned_prompt):
            self._debug_print("Matched prompt!")
        else:
            self._debug_print("No match.")

        try:
            self._test_channel_read(pattern=self.prompt_pattern)
        except Exception as e:
            self._debug_print(f"Exception during _test_channel_read: {repr(e)}")

        self.set_base_prompt()
        self.disable_paging(command="terminal length 0")
        self.set_terminal_width(command="terminal width 132")

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        if pattern is None:
            pattern = self.prompt_pattern
        self.write_channel("\n")
        time.sleep(0.5)
        prompt = self.find_prompt(delay_factor=delay_factor * 2)
        prompt = self._strip_prompt_garbage(prompt)
        self.base_prompt = prompt.strip(pri_prompt_terminator + alt_prompt_terminator)
        return self.base_prompt

    def check_enable_mode(self, check_string: str = "#") -> bool:
        return super().check_enable_mode(check_string=check_string)

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        output = ""
        msg = "Failed to enter enable mode. Verify 'secret' is set in ConnectHandler."
        if check_state and self.check_enable_mode():
            return output

        self.write_channel(self.normalize_cmd(cmd))
        try:
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(pattern=re.escape(cmd.strip()))
            output += self.read_until_prompt_or_pattern(pattern=pattern, re_flags=re_flags)
            if re.search(pattern, output):
                self.write_channel(self.normalize_cmd(self.secret))
                output += self.read_until_prompt()
            if not self.check_enable_mode():
                raise ValueError(msg)
        except NetmikoTimeoutException:
            raise ValueError(msg)
        return output

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        return super().exit_enable_mode(exit_command=exit_command)

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: Optional[str] = None,
        force_regex: bool = False,
    ) -> bool:
        if pattern is None:
            pattern = self.config_mode_prompt_pattern

        try:
            output = self.read_channel_timing(read_timeout=2.0)
            cleaned_output = self._strip_prompt_garbage(output)

            if force_regex:
                return bool(re.search(check_string, cleaned_output))
            else:
                pattern_match = bool(re.search(pattern, cleaned_output))
                string_match = check_string in cleaned_output
                return pattern_match or string_match

        except ReadTimeout:
            return False
        except Exception:
            return False

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: Optional[str] = None,
        re_flags: int = 0,
    ) -> str:
        if pattern is None:
            pattern = self.config_mode_prompt_pattern

        self.write_channel(self.normalize_cmd(config_command))
        time.sleep(2)
        output = self.read_channel()

        try:
            return super().config_mode(
                config_command=config_command,
                pattern=pattern,
                re_flags=re_flags,
            )
        except Exception:
            return output

    def exit_config_mode(
        self,
        exit_config: str = "exit",
        pattern: Optional[str] = None,
    ) -> str:
        if pattern is None:
            pattern = self.prompt_pattern

        output = ""

        if not self.check_config_mode():
            return output

        self.write_channel(self.normalize_cmd(exit_config))
        time.sleep(1)

        try:
            response = self.read_channel_timing(read_timeout=3.0)
            cleaned_response = self._strip_prompt_garbage(response)
            output += response

            confirmation_patterns = [
                r'[Aa]re you sure.*\?',
                r'[Cc]onfirm.*\?',
                r'\[y/n\]',
                r'\(y/n\)',
                r'[Yy]es/[Nn]o',
            ]

            needs_confirmation = any(re.search(pattern, cleaned_response, re.IGNORECASE)
                                     for pattern in confirmation_patterns)

            if needs_confirmation:
                self.write_channel("y\n")
                time.sleep(1)
                confirm_response = self.read_channel_timing(read_timeout=5.0)
                output += confirm_response

            time.sleep(1)
            final_check = self.read_channel_timing(read_timeout=2.0)
            output += final_check

            max_attempts = 3
            for _ in range(max_attempts):
                if not self.check_config_mode():
                    break
                else:
                    self.write_channel(self.normalize_cmd("end"))
                    time.sleep(1)
                    additional_output = self.read_channel_timing(read_timeout=3.0)
                    output += additional_output

        except Exception:
            try:
                self.write_channel(self.normalize_cmd("end"))
                time.sleep(2)
                fallback_output = self.read_channel_timing(read_timeout=3.0)
                output += fallback_output
            except:
                pass

        return output

    def save_config(
        self,
        cmd: str = "write memory",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        return super().save_config(
            cmd=cmd,
            confirm=confirm,
            confirm_response=confirm_response,
        )

    def find_prompt(self, delay_factor: float = 1.0) -> str:
        raw_prompt = super().find_prompt(delay_factor=delay_factor)
        return self._strip_prompt_garbage(raw_prompt)


class KontronOSSSH(KontronOSBase):
    pass


class KontronOSTelnet(KontronOSBase):
    pass
