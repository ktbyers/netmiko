"""
AsterNOS platforms running Enterprise SONiC Distribution by AsterFusion Co.
"""

from netmiko import log
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.no_enable import NoEnable
from typing import (
    Optional,
    Any,
    List,
    Dict,
    Sequence,
    Iterator,
    TextIO,
    Union,
    TYPE_CHECKING,
)


import threading
import time

if TYPE_CHECKING:
    from os import PathLike


class AsterfusionBase(NoEnable, CiscoSSHConnection):
    def __init__(self, cli_mode: str = "klish", **kwargs: Any) -> None:
        self.cli_mode = cli_mode
        super().__init__(**kwargs)
        self.close_thread_alive_check = False
        self.thread_alive()

    def thread_alive(self) -> None:
        check_alive_time = 120  # 120s send is_alive chr

        def send_alive() -> None:
            time.sleep(check_alive_time)  # wait connection is initialised
            while True:
                if self.close_thread_alive_check:
                    log.info(f"{self} session is close ,exit --  ")
                    break
                alive = self.is_alive()
                log.debug(f"[]check alive {self} {alive}")
                if (not alive) and (self.close_thread_alive_check):  # check 3 times
                    log.info(
                        f"{self} is not alive and close thread alive check , exit --"
                    )
                    break
                time.sleep(check_alive_time)  # alive check time
            return

        th = threading.Thread(target=send_alive, daemon=True)
        th.start()

    def close_alive_thread(self) -> None:
        self.close_thread_alive_check = True

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>$#]")
        self.set_base_prompt(alt_prompt_terminator="$")
        if self.cli_mode == "klish":
            self._enter_shell()
            self.disable_paging()
        elif self.cli_mode == "bash":
            self._enter_bash_cli()
        else:
            pass

    def config_mode(
        self,
        config_command: str = "configure terminal",
        pattern: str = r"\#",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def _enter_shell(self) -> str:
        log.debug(f"Host {self.host} {self.cli_mode} Enter sonic-cli shell")
        return self._send_command_str("sonic-cli", expect_string=r"\#")

    def _enter_bash_cli(self) -> str:
        log.debug(f"Host {self.host} {self.cli_mode} Enter bash shell")
        return self._send_command_str("system bash", expect_string=r"\$")

    def _enter_vtysh(self) -> str:
        log.debug(f"Host {self.host} {self.cli_mode} Enter vtysh shell")
        return self._send_command_str("vtysh", expect_string=r"\#")

    def disable_paging(
        self,
        command: str = "terminal raw-output",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        return super().disable_paging(
            command=command,
            delay_factor=delay_factor,
            cmd_verify=cmd_verify,
            pattern=pattern,
        )

    def write_config(self) -> str:
        return super().save_config(cmd="write", confirm=True, confirm_response="y")


class AsterfusionSSH(AsterfusionBase):
    def send_command(
        self,
        command_string: str,
        expect_string: Optional[str] = None,
        read_timeout: float = 10.0,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        auto_find_prompt: bool = True,
        strip_prompt: bool = True,
        strip_command: bool = True,
        normalize: bool = True,
        use_textfsm: bool = False,
        textfsm_template: Optional[str] = None,
        use_ttp: bool = False,
        ttp_template: Optional[str] = None,
        use_genie: bool = False,
        cmd_verify: bool = True,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        log.debug(
            "Host [{}], run cmd [{}] , find prompt: {} ".format(
                self.host, command_string, self.find_prompt()
            )
        )
        try:
            output = super().send_command(
                command_string,
                expect_string,
                read_timeout=read_timeout,
                delay_factor=delay_factor,
                max_loops=max_loops,
                auto_find_prompt=auto_find_prompt,
                strip_prompt=strip_prompt,
                strip_command=strip_command,
                normalize=normalize,
                use_textfsm=use_textfsm,
                textfsm_template=textfsm_template,
                use_ttp=use_ttp,
                ttp_template=ttp_template,
                use_genie=use_genie,
                cmd_verify=cmd_verify,
            )
            return output
        except Exception as e:
            log.debug(
                f"send_sonic_command got Exception, host:{self.host} , self: {self}"
            )
            return str(e)

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        **kwargs: Any,
    ) -> str:
        log.debug(
            "Host [{}], run cmd [{}] , find prompt: {} ".format(
                self.host, config_commands, self.find_prompt()
            )
        )
        output = super().send_config_set(config_commands, **kwargs)
        return output

    def send_config_from_file(
        self, config_file: Union[str, bytes, "PathLike[Any]"], **kwargs: Any
    ) -> str:
        """
        Send configuration commands down the SSH channel from a file.

        The file is processed line-by-line and each command is sent down the
        SSH channel.

        **kwargs are passed to send_config_set method.

        :param config_file: Path to configuration file to be sent to the device

        :param kwargs: params to be sent to send_config_set method
        """
        log.debug(
            "Host [{!r}] run cmd from file [{!r}] , find prompt: {!r} ".format(
                self.host, config_file, self.find_prompt()
            )
        )
        output = super().send_config_from_file(config_file, **kwargs)
        return output
