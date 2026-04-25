import re
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from netmiko.base_connection import BaseConnection

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.linux.linux_ssh import LinuxSSH
from netmiko.scp_handler import BaseFileTransfer


class ZpeNodegridSSH(NoEnable, NoConfig, LinuxSSH):
    """ZPE Systems Nodegrid SSH driver.

    The Nodegrid OS uses a directory-based virtual configuration tree.
    Navigation uses 'cd' and 'ls'; read operations use 'show'; configuration
    uses 'set param=value'. Changes are staged and indicated by a '+' prefix
    in the prompt until a 'commit' is issued. There is no traditional enable
    or config mode.

    Prompt examples::

        [admin@nodegrid /]#           Normal (no staged changes)
        [+admin@nodegrid ETH0]#       Staged changes pending commit

    The underlying Linux shell is accessible via 'shell'; 'exit' returns
    to the Nodegrid CLI.

    SSH login and CLI mode transitions example::

        [admin@nodegrid /]# cd /settings/network_connections/ETH0/
        [admin@nodegrid ETH0]# set ipv4_mode=static
        [+admin@nodegrid ETH0]# set ipv4_address=192.168.1.50
        [+admin@nodegrid ETH0]# commit
        [admin@nodegrid ETH0]#
    """

    # Matches: [admin@nodegrid /]# and [+admin@nodegrid ETH0]#
    prompt_pattern = r"\[\+?.*\]#"
    # Matches: root@nodegrid:/var/home# or admin@nodegrid:~$
    shell_prompt_pattern = r".+@.+:.+[\$#]"

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = "",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Set the base prompt using the Nodegrid prompt pattern."""
        if pattern is None:
            pattern = self.prompt_pattern
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

    def find_prompt(self, delay_factor: float = 1.0, pattern: Optional[str] = None) -> str:
        """Find the current prompt."""
        if pattern is None:
            pattern = self.prompt_pattern
        return super().find_prompt(delay_factor=delay_factor, pattern=pattern)

    def _prompt_handler(self, auto_find_prompt: bool) -> str:
        """Return the prompt regex used by send_command for output termination.

        Uses the broad prompt_pattern rather than the escaped base_prompt so
        that send_command works correctly after 'cd' changes the prompt.
        """
        return self.prompt_pattern

    def strip_prompt(self, a_string: str) -> str:
        """Strip the trailing Nodegrid prompt from command output.

        Uses regex rather than an exact base_prompt match to correctly handle
        prompt changes from directory navigation and the '+' staged-change
        indicator.
        """
        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]
        if re.search(self.prompt_pattern, last_line):
            return self.RESPONSE_RETURN.join(response_list[:-1])
        return a_string

    def disable_paging(
        self,
        command: str = ".sessionpageout undefined=no",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disable paging for the current CLI session.

        WARNING: Not officially documented by ZPE. Could negatively impact performance.
        """
        return self._send_command_str(command, expect_string=self.prompt_pattern)

    def commit(self) -> str:
        """Commit staged configuration changes."""
        return self._send_command_str("commit", expect_string=self.prompt_pattern, read_timeout=30)

    def _enter_shell(self) -> str:
        """Enter the Bash shell on ZPE Nodegrid."""
        return self._send_command_str("shell", expect_string=self.shell_prompt_pattern)

    def _return_cli(self) -> str:
        """Return to the ZPE Nodegrid CLI."""
        return self._send_command_str("exit", expect_string=self.prompt_pattern)


class ZpeNodegridFileTransfer(BaseFileTransfer):
    """ZPE Nodegrid SCP File Transfer driver."""

    ssh_ctl_chan: "ZpeNodegridSSH"

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
        search_pattern = self.ssh_ctl_chan.shell_prompt_pattern
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system."""
        return self._check_file_exists_unix(
            remote_cmd=remote_cmd, search_pattern=self.ssh_ctl_chan.shell_prompt_pattern
        )

    def remote_file_size(self, remote_cmd: str = "", remote_file: Optional[str] = None) -> int:
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(
            remote_cmd=remote_cmd,
            remote_file=remote_file,
            search_pattern=self.ssh_ctl_chan.shell_prompt_pattern,
        )

    def remote_md5(self, base_cmd: str = "md5sum", remote_file: Optional[str] = None) -> str:
        """Calculate remote MD5 and returns the hash."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_cmd = f"{base_cmd} {self.file_system}/{remote_file}"
        self.ssh_ctl_chan._enter_shell()
        try:
            output = self.ssh_ctl_chan._send_command_str(
                remote_cmd,
                expect_string=self.ssh_ctl_chan.shell_prompt_pattern,
                read_timeout=300,
            )
        finally:
            self.ssh_ctl_chan._return_cli()
        return self.process_md5(output.strip())

    @staticmethod
    def process_md5(md5_output: str, pattern: str = r"(\S+)\s+") -> str:
        """Process the string to retrieve the MD5 hash."""
        match = re.search(pattern, md5_output)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid output from MD5 command: {md5_output}")

    def enable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError

    def disable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError
