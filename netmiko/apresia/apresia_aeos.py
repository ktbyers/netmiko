from typing import Any, Optional
from netmiko.cisco_base_connection import CiscoSSHConnection


class ApresiaAeosBase(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging()

    def disable_paging(
        self,
        command: str = "terminal length 0",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:

        self.enable()
        check_command = f"show running-config | include {command}"
        show_run = self._send_command_str(check_command)

        output = ""
        if self.allow_auto_change and command not in show_run:
            output += super().disable_paging(
                command=command,
                delay_factor=delay_factor,
                cmd_verify=cmd_verify,
                pattern=pattern,
            )
        self.exit_enable_mode()
        return output


class ApresiaAeosSSH(ApresiaAeosBase):
    pass


class ApresiaAeosTelnet(ApresiaAeosBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)
