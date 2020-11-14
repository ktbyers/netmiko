import re
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoFileTransfer


class AristaBase(CiscoSSHConnection):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("fast_cli", True)
        kwargs.setdefault("_legacy_mode", False)
        return super().__init__(*args, **kwargs)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        cmd = "terminal width 511"
        # Arista will echo immediately and then when the device really responds (like NX-OS)
        self.set_terminal_width(command=cmd, pattern=r"Width set to")
        self.disable_paging(cmd_verify=False, pattern=r"Pagination disabled")
        self.set_base_prompt()

    def enable(
        self,
        cmd="enable",
        pattern="ssword",
        enable_pattern=r"\#",
        re_flags=re.IGNORECASE,
    ):
        return super().enable(
            cmd=cmd, pattern=pattern, enable_pattern=enable_pattern, re_flags=re_flags
        )

    def check_config_mode(self, check_string=")#", pattern=r"[>\#]"):
        """
        Checks if the device is in configuration mode or not.

        Arista, unfortunately, does this:
        loc1-core01(s1)#

        Can also be (s2)
        """
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=pattern)
        output = output.replace("(s1)", "")
        output = output.replace("(s2)", "")
        return check_string in output

    def config_mode(self, config_command="configure terminal", pattern="", re_flags=0):
        """Force arista to read pattern all the way to prompt on the next line."""

        if not re_flags:
            re_flags = re.DOTALL
        check_string = re.escape(")#")

        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
            pattern = f"{pattern}.*{check_string}"
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def _enter_shell(self):
        """Enter the Bourne Shell."""
        return self.send_command("bash", expect_string=r"[\$#]")

    def _return_cli(self):
        """Return to the CLI."""
        return self.send_command("exit", expect_string=r"[#>]")


class AristaSSH(AristaBase):
    pass


class AristaTelnet(AristaBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)


class AristaFileTransfer(CiscoFileTransfer):
    """Arista SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn,
        source_file,
        dest_file,
        file_system="/mnt/flash",
        direction="put",
        **kwargs,
    ):
        return super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            **kwargs,
        )

    def remote_space_available(self, search_pattern=""):
        """Return space available on remote device."""
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        return self._check_file_exists_unix(remote_cmd=remote_cmd)

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(
            remote_cmd=remote_cmd, remote_file=remote_file
        )

    def remote_md5(self, base_cmd="verify /md5", remote_file=None):
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_md5_cmd = f"{base_cmd} file:{self.file_system}/{remote_file}"
        dest_md5 = self.ssh_ctl_chan.send_command(
            remote_md5_cmd, max_loops=750, delay_factor=4
        )
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
