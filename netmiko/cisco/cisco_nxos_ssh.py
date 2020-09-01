import re
import os
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoFileTransfer


class CiscoNxosSSH(CiscoSSHConnection):
    def __init__(self, *args, **kwargs):
        # Cisco NX-OS defaults to fast_cli=True and legacy_mode=False
        kwargs.setdefault("fast_cli", True)
        kwargs.setdefault("_legacy_mode", False)
        return super().__init__(*args, **kwargs)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.ansi_escape_codes = True
        # NX-OS has an issue where it echoes the command even though it hasn't returned the prompt
        self._test_channel_read(pattern=r"[>#]")
        self.set_terminal_width(
            command="terminal width 511", pattern=r"terminal width 511"
        )
        self.disable_paging()
        self.set_base_prompt()

    def normalize_linefeeds(self, a_string):
        """Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text."""
        newline = re.compile(r"(\r\r\n|\r\n)")
        # NX-OS fix for incorrect MD5 on 9K (due to strange <enter> patterns on NX-OS)
        return newline.sub(self.RESPONSE_RETURN, a_string).replace("\r", "\n")

    def check_config_mode(self, check_string=")#", pattern="#"):
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)


class CiscoNxosFileTransfer(CiscoFileTransfer):
    """Cisco NXOS SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn,
        source_file,
        dest_file,
        file_system="bootflash:",
        direction="put",
        socket_timeout=10.0,
        progress=None,
        progress4=None,
    ):
        self.ssh_ctl_chan = ssh_conn
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        if file_system:
            self.file_system = file_system
        else:
            raise ValueError("Destination file system must be specified for NX-OS")

        if direction == "put":
            self.source_md5 = self.file_md5(source_file)
            self.file_size = os.stat(source_file).st_size
        elif direction == "get":
            self.source_md5 = self.remote_md5(remote_file=source_file)
            self.file_size = self.remote_file_size(remote_file=source_file)
        else:
            raise ValueError("Invalid direction specified")

        self.socket_timeout = socket_timeout
        self.progress = progress
        self.progress4 = progress4

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            if not remote_cmd:
                remote_cmd = f"dir {self.file_system}{self.dest_file}"
            remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
            search_string = r"{}.*Usage for".format(self.dest_file)
            if "No such file or directory" in remote_out:
                return False
            elif re.search(search_string, remote_out, flags=re.DOTALL):
                return True
            else:
                raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == "get":
            return os.path.exists(self.dest_file)

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file

        if not remote_cmd:
            remote_cmd = f"dir {self.file_system}/{remote_file}"

        remote_out = self.ssh_ctl_chan.send_command(remote_cmd)
        if re.search("no such file or directory", remote_out, flags=re.I):
            raise IOError("Unable to find file on remote system")
        # Match line containing file name
        escape_file_name = re.escape(remote_file)
        pattern = r".*({}).*".format(escape_file_name)
        match = re.search(pattern, remote_out)
        if match:
            file_size = match.group(0)
            file_size = file_size.split()[0]
            return int(file_size)

        raise IOError("Unable to find file on remote system")

    @staticmethod
    def process_md5(md5_output, pattern=r"= (.*)"):
        """Not needed on NX-OS."""
        raise NotImplementedError

    def remote_md5(self, base_cmd="show file", remote_file=None):
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        remote_md5_cmd = f"{base_cmd} {self.file_system}{remote_file} md5sum"
        return self.ssh_ctl_chan.send_command(remote_md5_cmd, max_loops=1500).strip()

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
