from netmiko.supermicro.smci_base_connection import SmciBaseConnection
from netmiko.scp_handler import BaseFileTransfer


class SmciSwitchUspSSH(SmciBaseConnection):
    pass


class SmciSwitchUspTelnet(SmciBaseConnection):
    pass


class SmciSwitchUspSerial(SmciBaseConnection):
    pass


class SmciSwitchUspFileTransfer(BaseFileTransfer):
    """Supermicro SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn,
        source_file,
        dest_file,
        file_system="/mnt",
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
