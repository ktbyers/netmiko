from typing import Any, Union, List, Dict, Optional, Callable
import re
import os

from netmiko.no_enable import NoEnable
from netmiko.no_config import NoConfig
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer


class MikrotikBase(NoEnable, NoConfig, CiscoSSHConnection):
    """Common Methods for Mikrotik RouterOS and SwitchOS"""

    prompt_pattern = r"\].*>"

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r\n"

        return super().__init__(**kwargs)

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        # Mikrotik might prompt to read software licenses before displaying the initial prompt.
        license_prompt = "Do you want to see the software license"
        combined_pattern = rf"(?:{self.prompt_pattern}|{license_prompt})"
        data = self.read_until_pattern(pattern=combined_pattern, re_flags=re.I)
        if license_prompt in data:
            self.write_channel("n")
            self.read_until_pattern(pattern=self.prompt_pattern)

    def session_preparation(self, *args: Any, **kwargs: Any) -> None:
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        self.set_base_prompt()

    def _modify_connection_params(self) -> None:
        """Append login options to username
        c: disable console colors
        e: enable dumb terminal mode
        t: disable auto detect terminal capabilities
        511w: set term width
        4098h: set term height
        """
        self.username += "+ct511w4098h"

    def disable_paging(self, *args: Any, **kwargs: Any) -> str:
        """Mikrotik does not have paging by default."""
        return ""

    def strip_prompt(self, a_string: str) -> str:
        """Strip the trailing router prompt from the output.

        Mikrotik just does a lot of formatting/has ansi escape codes in output so
        we need a special handler here.

        There can be two trailing instances of the prompt probably due to
        repainting.
        """
        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]

        # Drop the first trailing prompt
        if self.base_prompt in last_line:
            a_string = self.RESPONSE_RETURN.join(response_list[:-1])
            a_string = a_string.rstrip()
            # Now it should be just normal: call the parent method
            a_string = super().strip_prompt(a_string)
            return a_string.strip()
        else:
            # Unexpected just return the original string
            return a_string

    def strip_command(self, command_string: str, output: str) -> str:
        """
        Mikrotik can echo the command multiple times :-(

        Example:
        system routerboard print
        [admin@MikroTik] > system routerboard print
        """
        output = super().strip_command(command_string, output)
        cmd = command_string.strip()

        output = output.lstrip()
        # '[admin@MikroTik] > cmd' then the first newline should be matched
        pattern = rf"^\[.*\] > {re.escape(cmd)}.*${self.RESPONSE_RETURN}"
        if re.search(pattern, output, flags=re.M):
            output_lines = re.split(pattern, output, flags=re.M)
            new_output = output_lines[1:]
            return self.RESPONSE_RETURN.join(new_output)
        else:
            # command_string isn't there; do nothing
            return output

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """Strip the trailing space off."""
        prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        prompt = prompt.strip()
        self.base_prompt = prompt
        return self.base_prompt

    def send_command_timing(  # type: ignore
        self,
        command_string: str,
        cmd_verify: bool = True,
        **kwargs: Any,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """Force cmd_verify to be True due to all of the line repainting"""
        return super().send_command_timing(
            command_string=command_string, cmd_verify=cmd_verify, **kwargs
        )


class MikrotikRouterOsSSH(MikrotikBase):
    """Mikrotik RouterOS SSH driver."""

    pass


class MikrotikSwitchOsSSH(MikrotikBase):
    """Mikrotik SwitchOS SSH driver."""

    pass


class MikrotikRouterOsFileTransfer(BaseFileTransfer):
    """Mikrotik Router Os File Transfer driver."""

    def __init__(
        self,
        ssh_conn: BaseConnection,
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = "flash",
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

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system."""
        if self.direction == "put":
            if not remote_cmd:
                remote_cmd = f'/file print detail where name="{self.file_system}/{self.dest_file}"'
            remote_out = self.ssh_ctl_chan._send_command_timing_str(remote_cmd)
            # Output will look like
            # 0 name="flash/test9.txt" type=".txt file" size=19 creation-time=jun...
            # fail case will be blank line (all whitespace)
            if (
                "size" in remote_out
                and f"{self.file_system}/{self.dest_file}" in remote_out
            ):
                return True
            elif not remote_out.strip():
                return False
            raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == "get":
            return os.path.exists(self.dest_file)
        else:
            raise ValueError("Unexpected value for self.direction")

    def remote_space_available(self, search_pattern: str = "") -> int:
        """Return space available on remote device."""
        remote_cmd = "system resource print without-paging"
        sys_res = self.ssh_ctl_chan._send_command_timing_str(remote_cmd).splitlines()
        for res in sys_res:
            if "free-memory" in res:
                spaceMib = res.strip().replace("free-memory: ", "").replace("MiB", "")
                return int(float(spaceMib) * 1048576)
        raise ValueError("Unexpected output from remote_space_available")

    def remote_file_size(
        self, remote_cmd: str = "", remote_file: Optional[str] = None
    ) -> int:
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
            else:
                raise ValueError("Invalid value for file transfer direction.")

        if not remote_cmd:
            remote_cmd = (
                f'/file print detail where name="{self.file_system}/{remote_file}"'
            )
        remote_out = self.ssh_ctl_chan._send_command_timing_str(remote_cmd)
        try:
            size = remote_out.split("size=")[1].split(" ")[0]
            return self._format_to_bytes(size)
        except (KeyError, IndexError):
            raise ValueError("Unable to find file on remote system")

    def file_md5(self, file_name: str, add_newline: bool = False) -> str:
        raise AttributeError(
            "RouterOS does not natively support an MD5-hash operation."
        )

    @staticmethod
    def process_md5(md5_output: str, pattern: str = "") -> str:
        raise AttributeError(
            "RouterOS does not natively support an MD5-hash operation."
        )

    def compare_md5(self) -> bool:
        raise AttributeError(
            "RouterOS does not natively support an MD5-hash operation."
        )

    def remote_md5(self, base_cmd: str = "", remote_file: Optional[str] = None) -> str:
        raise AttributeError(
            "RouterOS does not natively support an MD5-hash operation."
        )

    def verify_file(self) -> bool:
        """
        Verify the file has been transferred correctly based on filesize.
        This method is very approximate as Mikrotik rounds file sizes to KiB, MiB, GiB...
        Therefore multiple conversions from/to bytes are needed
        """
        if self.direction == "put":
            local_size = self._format_bytes(os.stat(self.source_file).st_size)
            remote_size = self._format_bytes(
                self.remote_file_size(remote_file=self.dest_file)
            )
            return local_size == remote_size
        elif self.direction == "get":
            local_size = self._format_bytes(os.stat(self.dest_file).st_size)
            remote_size = self._format_bytes(
                self.remote_file_size(remote_file=self.source_file)
            )
            return local_size == remote_size
        else:
            raise ValueError("Unexpected value of self.direction")

    @staticmethod
    def _format_to_bytes(size: str) -> int:
        """
        Internal function to convert Mikrotik size to bytes
        """
        if size.endswith("KiB"):
            return round(int(float(size.replace("KiB", "")) * 1024))
        if size.endswith("MiB"):
            return round(int(float(size.replace("MiB", "")) * 1048576))
        if size.endswith("GiB"):
            return round(int(float(size.replace("GiB", "")) * 1073741824))
        return round(int(size))

    @staticmethod
    def _format_bytes(size: int) -> str:
        """
        Internal function to convert bytes to KiB, MiB or GiB
        Extremely approximate
        """
        n = 0
        levels = {0: "", 1: "Ki", 2: "Mi", 3: "Gi"}
        while size > 4096 and n < 3:
            size = round(size / 1024)
            n += 1
        return f"{size}{levels[n]}B"
