from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.cisco_base_connection import CiscoFileTransfer
from netmiko import log


class AristaBase(CiscoSSHConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string=')#', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Arista, unfortunately, does this:
        loc1-core01(s1)#

        Can also be (s2)
        """
        log.debug("pattern: {0}".format(pattern))
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=pattern)
        log.debug("check_config_mode: {0}".format(repr(output)))
        output = output.replace("(s1)", "")
        output = output.replace("(s2)", "")
        log.debug("check_config_mode: {0}".format(repr(output)))
        return check_string in output

    def _enter_shell(self):
        """Enter the Bourne Shell."""
        return self.send_command('bash', expect_string=r"[\$#]")

    def _return_cli(self):
        """Return to the CLI."""
        return self.send_command('exit', expect_string=r"[#>]")


class AristaSSH(AristaBase):
    pass


class AristaTelnet(AristaBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get('default_enter')
        kwargs['default_enter'] = '\r\n' if default_enter is None else default_enter
        super(AristaTelnet, self).__init__(*args, **kwargs)


class AristaFileTransfer(CiscoFileTransfer):
    """Arista SCP File Transfer driver."""
    def __init__(self, ssh_conn, source_file, dest_file, file_system="/mnt/flash", direction='put'):
        return super(AristaFileTransfer, self).__init__(ssh_conn=ssh_conn,
                                                        source_file=source_file,
                                                        dest_file=dest_file,
                                                        file_system=file_system,
                                                        direction=direction)

    def remote_space_available(self, search_pattern=""):
        """Return space available on remote device."""
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        return self._check_file_exists_unix(remote_cmd=remote_cmd)

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(remote_cmd=remote_cmd, remote_file=remote_file)

    def remote_md5(self, base_cmd='verify /md5', remote_file=None):
        if remote_file is None:
            if self.direction == 'put':
                remote_file = self.dest_file
            elif self.direction == 'get':
                remote_file = self.source_file
        remote_md5_cmd = "{} file:{}/{}".format(base_cmd, self.file_system, remote_file)
        dest_md5 = self.ssh_ctl_chan.send_command(remote_md5_cmd, max_loops=750, delay_factor=4)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
