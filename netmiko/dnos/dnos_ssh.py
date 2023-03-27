import re
from typing import Any, Iterator, Optional, Sequence, TextIO, Union

from netmiko.base_connection import BaseConnection
from netmiko.exceptions import ReadTimeout
from netmiko.scp_handler import BaseFileTransfer


class DnosSSH(BaseConnection):
    """Drivenets OS support for netmiko"""

    exec_prompt = r"[$>#]"
    root_prompt = r"(?m:]#\s*$)"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=self.exec_prompt)
        self.disable_paging(cmd_verify=False, command="set cli-terminal-length 0")
        self.set_base_prompt(alt_prompt_terminator="")

    def check_enable_mode(self, check_string: str = "#") -> bool:
        """Check if in enable mode. Return boolean."""
        # overriding the enable mode method, always return true as enable
        # mode is not available in dnos
        return True

    def commit(
        self,
        confirm: bool = False,
        confirm_delay: Optional[int] = None,
        comment: str = "",
        read_timeout: float = 120.0,
        and_quit: bool = False,
    ) -> str:
        """
        Commit the candidate configuration.

        confirm: Confirm the commit after a default timeout of 10 minutes
        confirm_delay: Set the delay for the commit confirm operation
        comment: Set the log for the commit operation
        """
        if confirm_delay and not confirm:
            raise ValueError("Invalid arguments supplied to DNOS commit")
        if comment:
            comment_string = f" log {comment}"
        else:
            comment_string = ""

        if confirm and confirm_delay:
            command_string = f"commit confirm {confirm_delay}{comment_string}"
        elif confirm:
            command_string = f"commit confirm{comment_string}"
        elif and_quit:
            command_string = f"commit and-exit{comment_string}"
        else:
            command_string = f"commit{comment_string}"

        error_marker = "ERROR:"
        warning_marker = "Warning:"

        # Enter config mode (if necessary)
        output = self.config_mode()

        expect_string = (
            re.escape(self.base_prompt)
            if and_quit
            else rf"#|{error_marker}|{warning_marker}"
        )

        output += self._send_command_str(
            command_string,
            expect_string=expect_string,
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
        )

        if error_marker in output:
            raise ValueError(
                f"Commit failed with the following \
                             errors:\n\n{output}"
            )
        if warning_marker in output:
            # Other commits occurred, don't proceed with commit
            output += self._send_command_timing_str(
                "abort", strip_prompt=False, strip_command=False, cmd_verify=False
            )
            raise ValueError(
                f"Commit failed with the following \
                             errors:\n\n{output}"
            )

        return output

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode."""
        # overriding the enable mode method, do nothing as enable mode is not
        # available in dnos
        return ""

    def exit_enable_mode(self, exit_command: str = "disable") -> str:
        """Exits enable (privileged exec) mode."""
        # overriding the enable mode method, do nothing as enable mode is not
        # available in dnos
        return ""

    def check_config_mode(
        self, check_string: str = "(cfg)#", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        *,
        exit_config_mode: bool = True,
        read_timeout: Optional[float] = None,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = "configure",
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
        error_pattern: str = "",
        terminator: str = r"#",
        bypass_commands: Optional[str] = None,
    ) -> str:
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            read_timeout=read_timeout,
            delay_factor=delay_factor,
            max_loops=max_loops,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            config_mode_command=config_mode_command,
            cmd_verify=cmd_verify,
            enter_config_mode=enter_config_mode,
            error_pattern=error_pattern,
            terminator=terminator,
            bypass_commands=bypass_commands,
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "") -> str:
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_shell_mode(self) -> bool:
        """Check if in shell mode. Return boolean."""
        return super().check_config_mode(
            check_string=self.root_prompt, force_regex=True
        )

    def find_prompt(
        self, delay_factor: float = 1.0, pattern: Optional[str] = None
    ) -> str:
        """
        Updates the find_prompt to workaround the default prompt on the
        DNOS shell.
        """
        prompt = super().find_prompt(delay_factor=delay_factor, pattern=pattern)
        # regex to filter out the date, time and namespace from the prompt
        # in the container shell
        date_time_ns_regex = r"\/\[.*\]\[.*\]"
        if re.search(date_time_ns_regex, prompt):
            return re.sub(date_time_ns_regex, "", prompt)[-1]
        else:
            return prompt

    def _enter_shell(self) -> str:
        """Enter the Bourne Shell of the routing-engine container on the
        active NCC"""

        cmd: str = "run start shell ncc active"
        output: str = ""
        pattern: str = "ssword"
        msg = "Failed to enter the shell mode"
        re_flags = re.IGNORECASE
        self.write_channel(self.normalize_cmd(cmd))
        #  pattern to detect the shell or password prompt in dnos
        prompt_or_password = rf"({self.root_prompt}|{pattern})"
        output += self.read_until_pattern(pattern=prompt_or_password)
        if re.search(pattern, output, flags=re_flags):
            self.write_channel(self.normalize_cmd(str(self.password)))
            try:
                output += self.read_until_pattern(pattern=rf"{self.root_prompt}")
            except ReadTimeout:
                raise ValueError(msg)
        # Nature of prompt will change after logging to the shell
        # setting the alt terminator to `:` as we remove the # while looking
        # for prompt in `find_prompt`
        # the hash is removed to make sure send_command method can find the
        # end of the command while in shell mode
        self.set_base_prompt(pattern=rf"{self.root_prompt}", alt_prompt_terminator=":")
        return output

    def _return_cli(self) -> str:
        """Return to the CLI."""
        output = self._send_command_str("exit", expect_string=r"[#]")
        self.set_base_prompt(alt_prompt_terminator="")
        return output


class DnosFileTransfer(BaseFileTransfer):
    def __init__(
        self,
        ssh_conn: "BaseConnection",
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = "/config/",
        direction: str = "put",
        **kwargs: Any,
    ) -> None:
        return super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            **kwargs,
        )

    def remote_space_available(self, search_pattern: str = "") -> int:
        """Return space available on remote device."""
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system
        (return boolean)."""
        return self._check_file_exists_unix(remote_cmd=remote_cmd)

    def remote_file_size(
        self, remote_cmd: str = "", remote_file: Optional[str] = None
    ) -> int:
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(
            remote_cmd=remote_cmd, remote_file=remote_file
        )

    def enable_scp(self, cmd: Union[str, Sequence[str], None] = None) -> None:
        raise NotImplementedError

    def disable_scp(self, cmd: Union[str, Sequence[str], None] = None) -> None:
        raise NotImplementedError

    @staticmethod
    def process_md5(md5_output: str, pattern: str = "") -> str:
        """
        Process the string to retrieve the MD5 hash, pattern arg is not used

        Output from DNOS in shell mode
        d41d8cd98f00b204e9800998ecf8427e  /config/test.txt
        """
        md5_split_output = md5_output.split()
        if len(md5_split_output) == 2:
            return md5_split_output[0]
        else:
            raise ValueError(f"Invalid output from MD5 command: {md5_output}")

    def remote_md5(
        self, base_cmd: str = "md5sum", remote_file: Optional[str] = None
    ) -> str:
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_md5_cmd = f"{base_cmd} {self.file_system}{remote_file}"
        # md5sum only available in shell
        self.ssh_ctl_chan._enter_shell()
        dest_md5 = self.ssh_ctl_chan._send_command_str(remote_md5_cmd, read_timeout=600)
        # exiting the shell mode
        self.ssh_ctl_chan._return_cli()
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5
