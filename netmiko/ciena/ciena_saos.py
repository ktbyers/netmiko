"""Ciena SAOS support."""
from __future__ import print_function
from __future__ import unicode_literals
import time
from netmiko.base_connection import BaseConnection



class CienaSaosBase(BaseConnection):
    """
    Ciena SAOS support.
    
    Implements methods for interacting Ciena Saos devices.
    
    Disables enable(), check_enable_mode(), config_mode() and
    check_config_mode()
    """

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="system shell session set more off")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def _enter_shell(self):
        """Enter the Bourne Shell."""
        return self.send_command("start shell sh", expect_string=r"[\$#]")

    def _return_cli(self):
        """Return to the Ciena SAOS CLI."""
        return self.send_command("exit", expect_string=r"[>]")

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Ciena SAOS."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on Ciena SAOS."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Ciena SAOS."""
        pass

    def check_config_mode(self, check_string="]"):
        """No config mode on Ciena SAOS."""
        pass

    def config_mode(self, config_command="configure"):
        """No config mode on Ciena SAOS."""
        pass

    def exit_config_mode(self, exit_config="exit configuration-mode"):
        """No config mode on Ciena SAOS."""
        pass

    def save_config(self, cmd="configuration save", confirm=False, confirm_response=""):
        """Saves Config."""
        output = self.send_command(command_string=cmd)
        return output

class CienaSaosSSH(CienaSaosBase):
    pass


class CienaSaosTelnet(CienaSaosBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super(CienaSaosTelnet, self).__init__(*args, **kwargs)
        
class CienaSaosFileTransfer(BaseFileTransfer):
    """Ciena SAOS SCP File Transfer driver."""

    def __init__(
        self, ssh_conn, source_file, dest_file, file_system="/var/tmp", direction="put"
    ):
        return super(CienaSaosFileTransfer, self).__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
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

    def remote_md5(self, base_cmd="file checksum md5", remote_file=None):
        return super(CienaSaosTransfer, self).remote_md5(
            base_cmd=base_cmd, remote_file=remote_file
        )

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
