"""Extreme support."""
import os
from typing import Any, Callable, Optional, Union, List, Dict
import re
from netmiko.base_connection import BaseConnection
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer


class ExtremeExosBase(NoConfig, CiscoSSHConnection):
    """Extreme Exos support.

    Designed for EXOS >= 15.0
    """

    def session_preparation(self) -> None:
        self._test_channel_read(pattern=r"[>\#]")
        self.set_base_prompt()
        self.disable_paging(command="disable clipaging")
        self.send_command_timing("disable cli prompting")

    def set_base_prompt(self, *args: Any, **kwargs: Any) -> str:
        """
        Extreme attaches an id to the prompt. The id increases with every command.
        It needs to br stripped off to match the prompt. Eg.

            testhost.1 #
            testhost.2 #
            testhost.3 #

        If new config is loaded and not saved yet, a '* ' prefix appears before the
        prompt, eg.

            * testhost.4 #
            * testhost.5 #
        """
        cur_base_prompt = super().set_base_prompt(*args, **kwargs)
        # Strip off any leading * or whitespace chars; strip off trailing period and digits
        match = re.search(r"[\*\s]*(.*)\.\d+", cur_base_prompt)
        if match:
            self.base_prompt = match.group(1)
            return self.base_prompt
        else:
            return self.base_prompt

    def send_command(
        self, *args: Any, **kwargs: Any
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """Extreme needs special handler here due to the prompt changes."""

        # Change send_command behavior to use self.base_prompt
        kwargs.setdefault("auto_find_prompt", False)

        # refresh self.base_prompt
        self.set_base_prompt()
        return super().send_command(*args, **kwargs)

    def save_config(
        self,
        cmd: str = "save configuration primary",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves configuration."""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )


class ExtremeExosSSH(ExtremeExosBase):
    pass


class ExtremeExosTelnet(ExtremeExosBase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)


class ExtremeExosFileTransfer(BaseFileTransfer):
    """Extreme EXOS SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn: BaseConnection,
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = "/usr/local/cfg",
        direction: str = "put",
        socket_timeout: float = 10.0,
        progress: Optional[Callable[..., Any]] = None,
        progress4: Optional[Callable[..., Any]] = None,
        hash_supported: bool = False,
    ) -> None:
        super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            socket_timeout=socket_timeout,
            progress=progress,
            progress4=progress4,
            hash_supported=hash_supported,
        )

    def remote_space_available(self, search_pattern: str = r"(\d+)\s+\d+%$") -> int:
        """Return space available on remote device."""
        remote_cmd = f"ls {self.file_system}"
        remote_output = self.ssh_ctl_chan._send_command_str(remote_cmd)
        if (
            "Invalid pathname" in remote_output
            or "No such file or directory" in remote_output
        ):
            msg = f"Invalid file_system: {self.file_system}"
        else:
            match = re.search(search_pattern, remote_output)
            if match:
                return int(match.group(1))
            else:
                msg = f"pattern: {search_pattern} not detected in output:\n\n{remote_output}"
        raise ValueError(msg)

    def verify_space_available(self, search_pattern: str = r"(\d+)\s+\d+%$") -> bool:
        """Verify sufficient space is available on destination file system (return boolean)."""
        return super().verify_space_available(search_pattern)

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            if not remote_cmd:
                remote_cmd = f"ls {self.file_system}/{self.dest_file}"
            remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
            if (
                "No such file or directory" in remote_out
                or "Invalid pathname" in remote_out
            ):
                return False
            elif self.dest_file in remote_out:
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
        if not remote_cmd:
            remote_cmd = f"ls {self.file_system}/{remote_file}"
        remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)
        assert isinstance(remote_file, str)
        escape_file_name = re.escape(remote_file)
        pattern = r".*({}).*".format(escape_file_name)
        match = re.search(pattern, remote_out)
        if match:
            line = match.group(0)
            # Format will be: -rw-r--r--    1 admin    admin     3934 Jan 24 03:50 filename
            # Format will be: "-rw-r--r--    1 admin    admin     3934 Jan 24  2022 filename"
            file_size = line.split()[4]
        else:
            raise IOError("Unable to parse 'ls' output in remote_file_size method")
        if (
            "No such file or directory" in remote_out
            or "Invalid pathname" in remote_out
        ):
            raise IOError("Unable to find file on remote system")
        else:
            return int(file_size)

    def file_md5(self, file_name: str, add_newline: bool = False) -> str:
        msg = "EXOS does not support an MD5-hash operation."
        raise AttributeError(msg)

    @staticmethod
    def process_md5(md5_output: str, pattern: str = "") -> str:
        msg = "EXOS does not support an MD5-hash operation."
        raise AttributeError(msg)

    def compare_md5(self) -> bool:
        msg = "EXOS does not support an MD5-hash operation."
        raise AttributeError(msg)

    def remote_md5(self, base_cmd: str = "", remote_file: Optional[str] = None) -> str:
        msg = "EXOS does not support an MD5-hash operation."
        raise AttributeError(msg)

    def enable_scp(self, cmd: str = "") -> None:
        msg = "EXOS does not support an enable SCP operation. SCP is always enabled."
        raise AttributeError(msg)

    def disable_scp(self, cmd: str = "") -> None:
        msg = "EXOS does not support a disable SCP operation."
        raise AttributeError(msg)

    def verify_file(self) -> bool:
        """Verify the file has been transferred correctly based on filesize."""
        if self.direction == "put":
            return os.stat(self.source_file).st_size == self.remote_file_size(
                remote_file=self.dest_file
            )
        elif self.direction == "get":
            return (
                self.remote_file_size(remote_file=self.source_file)
                == os.stat(self.dest_file).st_size
            )
        else:
            raise ValueError("Unexpected value of self.direction")
