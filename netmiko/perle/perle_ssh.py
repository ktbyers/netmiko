import re
from typing import Any, Dict, List, Optional, Union

from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.no_config import NoConfig
from netmiko.utilities import structured_data_converter


class PerleIolanSSH(NoConfig, CiscoBaseConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.default_enter = kwargs.get("default_enter", "\r")

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt(alt_prompt_terminator="$")

    def enable(
        self,
        cmd: str = "admin",
        pattern: str = "ssword:",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        return super().enable(cmd, pattern, enable_pattern, check_state, re_flags)

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        # Perle does not have this concept
        return ""

    def save_config(
        self, cmd: str = "save", confirm: bool = True, confirm_response: str = "y"
    ) -> str:
        return super().save_config(cmd, confirm, confirm_response)

    def send_command_timing(
        self,
        command_string: str,
        *args: Any,
        **kwargs: Any,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        real_command_string = command_string
        real_strip_command = kwargs.get("strip_command", True)
        real_strip_prompt = kwargs.get("strip_prompt", True)
        command = command_string
        more = r"< Hit any key >"
        kwargs["strip_prompt"] = False
        kwargs["strip_command"] = False

        output = str(super().send_command_timing(command_string, *args, **kwargs))

        command_string = " "
        kwargs["normalize"] = False
        kwargs["strip_command"] = True
        while more in output:
            output = re.sub(r"\n" + more, "", output)
            output += str(
                super().send_command_timing(
                    command_string,
                    *args,
                    **kwargs,
                )
            )

        output = self._sanitize_output(
            output,
            strip_command=real_strip_command,
            command_string=command,
            strip_prompt=real_strip_prompt,
        )
        return_data = structured_data_converter(
            command=real_command_string,
            raw_data=output,
            platform=self.device_type,
            use_textfsm=kwargs.get("use_textfsm", False),
            use_ttp=kwargs.get("use_ttp", False),
            use_genie=kwargs.get("use_genie", False),
            textfsm_template=kwargs.get("textfsm_template", None),
            ttp_template=kwargs.get("ttp_template", None),
            raise_parsing_error=kwargs.get("raise_parsing_error", False),
        )

        return return_data

    def strip_prompt(self, a_string: str) -> str:
        # Delete repeated prompts
        old_string = a_string
        while (a_string := super().strip_prompt(a_string)) != old_string:
            old_string = a_string
        return a_string

    def cleanup(self, command: str = "logout") -> None:
        return super().cleanup(command)
