"""
Aruba OS support.

For use with Aruba OS Controllers.

"""

import os
from typing import Any, Optional

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer


class ArubaOsSSH(CiscoSSHConnection):
    """Aruba OS support"""

    def __init__(self, **kwargs: Any) -> None:
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r"
        # Aruba has an auto-complete on space behavior that is problematic
        if kwargs.get("global_cmd_verify") is None:
            kwargs["global_cmd_verify"] = False
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        """Aruba OS requires enable mode to disable paging."""
        # Aruba switches output ansi codes
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no paging")

    def check_config_mode(
        self,
        check_string: str = "(config) #",
        pattern: str = r"[>#]",
        force_regex: bool = False,
    ) -> bool:
        """
        Checks if the device is in configuration mode or not.

        Aruba uses "(<controller name>) (config) #" as config prompt
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self,
        config_command: str = "configure term",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Aruba auto completes on space so 'configure' needs fully spelled-out."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )


class ArubaOsFileTransfer(BaseFileTransfer):
    """Aruba OS SCP File Transfer driver"""

    def __init__(
        self,
        file_system: Optional[str] = "/mm/mynode",
        hash_supported: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            file_system=file_system, hash_supported=hash_supported, **kwargs
        )

    def file_md5(self, file_name: str, add_newline: bool = False) -> str:
        """Aruba OS does not support an MD5-hash operation."""
        raise NotImplementedError

    @staticmethod
    def process_md5(md5_output: str, pattern: str = "") -> str:
        """Aruba OS does not support an MD5-hash operation."""
        raise NotImplementedError

    def compare_md5(self) -> bool:
        """Aruba OS does not support an MD5-hash operation."""
        raise NotImplementedError

    def remote_md5(self, base_cmd: str = "", remote_file: Optional[str] = None) -> str:
        """Aruba OS does not support an MD5-hash operation."""
        raise NotImplementedError

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            if not remote_cmd:
                remote_cmd = f"dir search {self.dest_file.rpartition('/')[-1]}"
            remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)

            if "Cannot get directory information" in remote_out:
                return False

            # dir search default.cfg
            # -rw-r--r--    1 root     root 16283 Nov  9 12:25 default.cfg
            # -rw-r--r--    1 root     root 22927 May 25 12:21 default.cfg.2016-05-25_20-21-38
            # -rw-r--r--    2 root     root 19869 May  9 12:20 default.cfg.2016-05-09_12-20-22
            # Construct a list of the last column
            return self.dest_file in [
                fields[-1]
                for line in remote_out.splitlines()
                if (fields := line.split())
            ]

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

        assert isinstance(remote_file, str)
        remote_file_search = remote_file.rpartition("/")[-1]

        if not remote_cmd:
            remote_cmd = f"dir search {remote_file_search}"
        remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)

        if "Cannot get directory information" in remote_out:
            msg = "Unable to find file on remote system"
            raise IOError(msg)

        # dir search default.cfg
        # -rw-r--r--    1 root     root 16283 Nov  9 12:25 default.cfg
        # -rw-r--r--    1 root     root 22927 May 25 12:21 default.cfg.2016-05-25_20-21-38
        # -rw-r--r--    2 root     root 19869 May  9 12:20 default.cfg.2016-05-09_12-20-22
        for line in remote_out.splitlines():
            if line:
                fields = line.split()
                if len(fields) >= 5:
                    file_size = fields[4]
                    f_name = fields[-1]
                    if f_name == remote_file_search:
                        break
        else:
            msg = "Unable to find file on remote system"
            raise IOError(msg)

        try:
            return int(file_size)
        except ValueError as ve:
            msg = "Unable to parse remote file size, wrong field in use or malformed command output"
            raise IOError(msg) from ve

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

    def remote_space_available(self, search_pattern: str = "") -> int:
        """Return space available on remote device."""
        remote_cmd = "show storage"
        remote_output = self.ssh_ctl_chan._send_command_str(remote_cmd).strip()

        # show storage (df -h)
        # Filesystem                Size      Used Available Use% Mounted on
        # /dev/root                57.0M     54.6M      2.3M  96% /
        # /dev/usbdisk/1            3.9G    131.0M      3.8G   3% /mnt/usbdisk/1
        available_sizes = [
            fields[-3]
            for line in remote_output.splitlines()
            if (fields := line.split()) and fields[-1] == "/flash"
        ]

        if not available_sizes:
            msg = "Could not determine remote space available."
            raise ValueError(msg)

        space_available = 0
        # There is potentially more than one filesystem for /flash
        for available_size in available_sizes:
            size_names = ["B", "K", "M", "G", "T", "P", "E"]
            suffix = available_size[-1]
            size_str = available_size[:-1]

            if suffix not in size_names:
                msg = "Could not determine remote space available."
                raise ValueError(msg)

            try:
                size = float(size_str)
            except ValueError as ve:
                msg = "Could not determine remote space available."
                raise ValueError(msg) from ve

            space_available += size * (1024 ** size_names.index(suffix))

        return int(space_available)

    def enable_scp(self, cmd: str = "service scp") -> None:
        """Enable SCP on remote device."""
        super().enable_scp(cmd)

    def disable_scp(self, cmd: str = "no service scp") -> None:
        """Disable SCP on remote device."""
        super().disable_scp(cmd)
