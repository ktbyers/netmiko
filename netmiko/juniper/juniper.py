import re
import warnings
from typing import Optional, Any

from netmiko.no_enable import NoEnable
from netmiko.base_connection import BaseConnection, DELAY_FACTOR_DEPR_SIMPLE_MSG
from netmiko.scp_handler import BaseFileTransfer


class JuniperBase(NoEnable, BaseConnection):
    """
    Implement methods for interacting with Juniper Networks devices.

    methods.  Overrides several methods for Juniper-specific compatibility.
    """

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        pattern = r"[%>$#]"
        self._test_channel_read(pattern=pattern)
        self.enter_cli_mode()

        cmd = "set cli screen-width 511"
        self.set_terminal_width(command=cmd, pattern=r"Screen width set to")
        # Overloading disable_paging which is confusing
        self.disable_paging(
            command="set cli complete-on-space off",
            pattern=r"Disabling complete-on-space",
        )
        self.disable_paging(
            command="set cli screen-length 0", pattern=r"Screen length set to"
        )
        self.set_base_prompt()

    def _enter_shell(self) -> str:
        """Enter the Bourne Shell."""
        return self._send_command_str("start shell sh", expect_string=r"[\$#]")

    def _return_cli(self) -> str:
        """Return to the Juniper CLI."""
        return self._send_command_str("exit", expect_string=r"[#>]")

    def _determine_mode(self, data: str = "") -> str:
        """Determine whether in shell or CLI."""
        pattern = r"[%>$#]"
        if not data:
            self.write_channel(self.RETURN)
            data = self.read_until_pattern(pattern=pattern, read_timeout=10)

        shell_pattern = r"(?:root@|%|\$)"
        if re.search(shell_pattern, data):
            return "shell"
        elif ">" in data or "#" in data:
            return "cli"
        else:
            raise ValueError(f"Unexpected data returned for prompt: {data}")

    def enter_cli_mode(self) -> None:
        """Check if at shell prompt root@ and go into CLI."""
        mode = self._determine_mode()
        if mode == "shell":
            shell_pattern = r"(?:root@|%|\$)"
            self.write_channel(self.RETURN)
            cur_prompt = self.read_until_pattern(pattern=shell_pattern, read_timeout=10)
            if re.search(r"root@", cur_prompt) or re.search(r"^%$", cur_prompt.strip()):
                cli_pattern = r"[>#]"
                self.write_channel("cli" + self.RETURN)
                self.read_until_pattern(pattern=cli_pattern, read_timeout=10)
        return

    def check_config_mode(
        self,
        check_string: str = "]",
        pattern: str = r"(?m:[>#] $)",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        ?m = Use multiline matching

        Juniper unfortunately will use # as a message indicator when not in config mode
        For example, with commit confirmed.

        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "configure",
        pattern: str = r"(?s:Entering configuration mode.*\].*#)",
        re_flags: int = 0,
    ) -> str:
        """
        Enter configuration mode.

        ?s = enables re.DOTALL in regex pattern.
        """
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(
        self, exit_config: str = "exit configuration-mode", pattern: str = ""
    ) -> str:
        """Exit configuration mode."""
        output = ""
        if self.check_config_mode():
            confirm_msg = "Exit with uncommitted changes"
            pattern = rf"(?:>|{confirm_msg})"
            output = self._send_command_str(
                exit_config,
                expect_string=pattern,
                strip_prompt=False,
                strip_command=False,
            )
            if confirm_msg in output:
                output += self._send_command_str(
                    "yes", expect_string=r">", strip_prompt=False, strip_command=False
                )
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def commit(
        self,
        confirm: bool = False,
        confirm_delay: Optional[int] = None,
        check: bool = False,
        comment: str = "",
        and_quit: bool = False,
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
    ) -> str:
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        default:
            command_string = commit
        check and (confirm or confirm_dely or comment):
            Exception
        confirm_delay and no confirm:
            Exception
        confirm:
            confirm_delay option
            comment option
            command_string = commit confirmed or commit confirmed <confirm_delay>
        check:
            command_string = commit check

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        """

        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)
        if check and (confirm or confirm_delay or comment):
            raise ValueError("Invalid arguments supplied with commit check")
        if confirm_delay and not confirm:
            raise ValueError(
                "Invalid arguments supplied to commit method both confirm and check"
            )

        # Select proper command string based on arguments provided
        command_string = "commit"
        commit_marker = "commit complete"
        if check:
            command_string = "commit check"
            commit_marker = "configuration check succeeds"
        elif confirm:
            if confirm_delay:
                command_string = "commit confirmed " + str(confirm_delay)
            else:
                command_string = "commit confirmed"
            commit_marker = "commit confirmed will be automatically rolled back in"

        # wrap the comment in quotes
        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = f'"{comment}"'
            command_string += " comment " + comment

        if and_quit:
            command_string += " and-quit"

        # Enter config mode (if necessary)
        output = self.config_mode()
        # and_quit will get out of config mode on commit

        # hostname might change on commit, and-quit might result in exiting config mode.
        re_prompt = re.escape(self.base_prompt)
        expect_string = rf"(?:{re_prompt}|[>#])"
        output += self._send_command_str(
            command_string,
            expect_string=expect_string,
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
        )

        if commit_marker not in output:
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")

        return output

    def strip_prompt(self, *args: Any, **kwargs: Any) -> str:
        """Strip the trailing router prompt from the output."""
        a_string = super().strip_prompt(*args, **kwargs)
        return self.strip_context_items(a_string)

    def strip_context_items(self, a_string: str) -> str:
        """Strip Juniper-specific output.

        Juniper will also put a configuration context:
        [edit]

        and various chassis contexts:
        {master:0}, {backup:1}

        This method removes those lines.
        """
        strings_to_strip = [
            r"\[edit.*\]",
            r"\{master:?.*\}",
            r"\{backup:?.*\}",
            r"\{line.*\}",
            r"\{primary.*\}",
            r"\{secondary.*\}",
        ]

        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]
        for pattern in strings_to_strip:
            if re.search(pattern, last_line, flags=re.I):
                return self.RESPONSE_RETURN.join(response_list[:-1])
        return a_string

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        try:
            if self.check_config_mode():
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'exit' (command)
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)


class JuniperSSH(JuniperBase):
    pass


class JuniperTelnet(JuniperBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)


class JuniperFileTransfer(BaseFileTransfer):
    """Juniper SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn: "BaseConnection",
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = "/var/tmp",
        direction: str = "put",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            **kwargs,
        )

    def remote_space_available(self, search_pattern: str = "") -> int:
        """Return space available on remote device."""
        search_pattern = r"[%>$#]"
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system (return boolean)."""
        return self._check_file_exists_unix(remote_cmd=remote_cmd)

    def remote_file_size(
        self, remote_cmd: str = "", remote_file: Optional[str] = None
    ) -> int:
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(
            remote_cmd=remote_cmd, remote_file=remote_file
        )

    def remote_md5(
        self, base_cmd: str = "file checksum md5", remote_file: Optional[str] = None
    ) -> str:
        return super().remote_md5(base_cmd=base_cmd, remote_file=remote_file)

    def enable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError

    def disable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError
