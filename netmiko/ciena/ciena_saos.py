"""Ciena SAOS support."""
from typing import Optional, Any
import re
import os
from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer


class CienaSaosBase(NoEnable, NoConfig, BaseConnection):
    """
    Ciena SAOS support.

    Implements methods for interacting Ciena Saos devices.
    """

    prompt_pattern = r"[>#$]"

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "",
        alt_prompt_terminator: str = "",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Ciena can use '>', '$', '#' for prompt terminator depending on the device."""
        prompt = self.find_prompt(delay_factor=delay_factor)

        pattern = rf"^.+{self.prompt_pattern}$"
        if not re.search(pattern, prompt):
            raise ValueError(f"Router prompt not found: {repr(prompt)}")
        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]
        return self.base_prompt

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=self.prompt_pattern)
        self.set_base_prompt()
        self.disable_paging(command="system shell session set more off")

    def _enter_shell(self) -> str:
        """Enter the Bourne Shell."""
        output = self._send_command_str("diag shell", expect_string=self.prompt_pattern)
        if "SHELL PARSER FAILURE" in output:
            msg = "SCP support on Ciena SAOS requires 'diag shell' permissions"
            raise ValueError(msg)
        return output

    def _return_cli(self) -> str:
        """Return to the Ciena SAOS CLI."""
        return self._send_command_str("exit", expect_string=r"[>]")

    def save_config(
        self,
        cmd: str = "configuration save",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class CienaSaosSSH(CienaSaosBase):
    pass


class CienaSaosTelnet(CienaSaosBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)


class CienaSaosFileTransfer(BaseFileTransfer):
    """Ciena SAOS SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn: BaseConnection,
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = None,
        direction: str = "put",
        **kwargs: Any,
    ) -> None:
        if file_system is None:
            file_system = f"/tmp/users/{ssh_conn.username}"
        return super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            **kwargs,
        )

    def remote_space_available(self, search_pattern: str = "") -> int:
        """
        Return space available on Ciena SAOS

        Output should only have the file-system that matches {self.file_system}

        Filesystem           1K-blocks      Used Available Use% Mounted on
        tmpfs                  1048576       648   1047928   0% /tmp
        """
        remote_cmd = f"file vols -P {self.file_system}"
        remote_output = self.ssh_ctl_chan._send_command_str(remote_cmd)
        remote_output = remote_output.strip()
        err_msg = (
            f"Parsing error, unexpected output from {remote_cmd}:\n{remote_output}"
        )

        # First line is the header; file_system_line is the output we care about
        header_line, filesystem_line = remote_output.splitlines()

        filesystem, _, _, space_avail, *_ = header_line.split()
        if "Filesystem" != filesystem or "Avail" not in space_avail:
            # Filesystem 1K-blocks Used Available Use% Mounted on
            raise ValueError(err_msg)

        # Normalize output - in certain outputs ciena will line wrap (this fixes that)
        # Strip the extra newline
        # /dev/mapper/EN--VOL-config
        #                  4096      1476      2620  36% /etc/hosts
        filesystem_line = re.sub(r"(^\S+$)\n", r"\1", filesystem_line, flags=re.M)

        # Checks to make sure what was returned is what we expect
        _, k_blocks, used, space_avail, _, _ = filesystem_line.split()
        for integer_check in (k_blocks, used, space_avail):
            try:
                int(integer_check)
            except ValueError:
                raise ValueError(err_msg)

        return int(space_avail) * 1024

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            if not remote_cmd:
                remote_cmd = f"file ls {self.file_system}/{self.dest_file}"
            remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
            search_string = re.escape(f"{self.file_system}/{self.dest_file}")
            if "ERROR" in remote_out:
                return False
            elif re.search(search_string, remote_out):
                return True
            else:
                raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == "get":
            return os.path.exists(self.dest_file)
        else:
            raise ValueError("Unexpected value for self.direction")

    def remote_file_size(
        self, remote_cmd: str = "", remote_file: Optional[str] = None
    ) -> int:
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file

        remote_file = f"{self.file_system}/{remote_file}"

        if not remote_cmd:
            remote_cmd = f"file ls -l {remote_file}"

        remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)

        if "No such file or directory" in remote_out:
            raise IOError("Unable to find file on remote system")

        escape_file_name = re.escape(remote_file)
        pattern = r"^.* ({}).*$".format(escape_file_name)
        match = re.search(pattern, remote_out, flags=re.M)
        if match:
            # Format: -rw-r--r--  1 pyclass  wheel  12 Nov  5 19:07 /var/tmp/test3.txt
            line = match.group(0)
            file_size = line.split()[4]
            return int(file_size)

        raise ValueError(
            "Search pattern not found for remote file size during SCP transfer."
        )

    def remote_md5(self, base_cmd: str = "", remote_file: Optional[str] = None) -> str:
        """Calculate remote MD5 and returns the hash.

        This command can be CPU intensive on the remote device.
        """
        if base_cmd == "":
            base_cmd = "md5sum"
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file

        remote_md5_cmd = f"{base_cmd} {self.file_system}/{remote_file}"

        self.ssh_ctl_chan._enter_shell()
        dest_md5 = self.ssh_ctl_chan._send_command_str(
            remote_md5_cmd, expect_string=r"[$#>]"
        )
        self.ssh_ctl_chan._return_cli()
        dest_md5 = self.process_md5(dest_md5, pattern=r"([0-9a-f]+)\s+")
        return dest_md5

    def enable_scp(self, cmd: str = "system server scp enable") -> None:
        return super().enable_scp(cmd=cmd)

    def disable_scp(self, cmd: str = "system server scp disable") -> None:
        return super().disable_scp(cmd=cmd)
