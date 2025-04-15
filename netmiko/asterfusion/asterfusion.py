"""
AsterNOS platforms running Enterprise SONiC Distribution by AsterFusion Co.
"""
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
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.no_enable import NoEnable

if TYPE_CHECKING:
    from os import PathLike


class AsterfusionAsterNOSSSH(NoEnable, CiscoSSHConnection):
    prompt_pattern = r"[>$#]"

    def __init__(self, _cli_mode: str = "klish", **kwargs: Any) -> None:
        self._cli_mode = _cli_mode
        super().__init__(**kwargs)

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt(alt_prompt_terminator="$")
        if self.cli_mode == "klish":
            self._enter_shell()
            self.disable_paging()
        elif self.cli_mode == "bash":
            self._enter_bash_cli()

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
        return self._send_command_str("sonic-cli", expect_string=r"\#")

    def _enter_bash_cli(self) -> str:
        return self._send_command_str("system bash", expect_string=r"\$")

    def _enter_vtysh(self) -> str:
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

    def save_config(
        self,
        cmd: str = "write",
        confirm: bool = True,
        confirm_response: str = "y",
    ) -> str:
        return super().save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)


1664     def send_command(
1665         self,
1666         command_string: str,
1667         expect_string: Optional[str] = None,
1668         read_timeout: float = 10.0,
1669         delay_factor: Optional[float] = None,
1670         max_loops: Optional[int] = None,
1671         auto_find_prompt: bool = True,
1672         strip_prompt: bool = True,
1673         strip_command: bool = True,
1674         normalize: bool = True,
1675         use_textfsm: bool = False,
1676         textfsm_template: Optional[str] = None,
1677         use_ttp: bool = False,
1678         ttp_template: Optional[str] = None,
1679         use_genie: bool = False,
1680         cmd_verify: bool = True,
1681         raise_parsing_error: bool = False,
1682     ) -> Union[str, List[Any], Dict[str, Any]]:


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
        raise_parsing_error: bool = True,
    ) -> Union[str, List[Any], Dict[str, Any]]:
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
            raise_parsing_error=raise_parsing_error,
        )
        return output

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        **kwargs: Any,
    ) -> str:
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
        output = super().send_config_from_file(config_file, **kwargs)
        return output
