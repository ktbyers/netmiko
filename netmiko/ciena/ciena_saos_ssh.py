"""Ciena SAOS support."""
from __future__ import print_function
from __future__ import unicode_literals
import time
import re
import os
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer


class CienaSaosSSH(CiscoSSHConnection):
    """Ciena SAOS support."""

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging(command="system shell session set more off")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def _enter_shell(self):
        """Enter the Bourne Shell."""
        return self.send_command("diag shell", expect_string=r"[\$#]")

    def _return_cli(self):
        """Return to the Ciena SAOS CLI."""
        return self.send_command("exit", expect_string=r"[>]")


    def save_config(self, cmd="config save", confirm=False, confirm_response=""):
        """Save Configuration"""
        #output = self.send_command(command_string=cmd)
        return super(CienaSaosSSH, self).save_config(cmd=cmd, confirm=confirm, confirm_response=confirm_response)

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Ciena."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on Ciena."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Ciena."""
        pass        

    def check_config_mode(self, check_string=">", pattern=""):
        """Checks if the device is in configuration mode or not."""
        return super(CienaSaosSSH, self).check_config_mode(check_string=check_string)

    def config_mode(self, config_command="config"):
        """Enter configuration mode."""
        return super(CienaSaosSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config="exit"):
        """Exit configuration mode."""
        output = ""
        if self.check_config_mode():
            output = self.send_command_timing(
                exit_config, strip_prompt=False, strip_command=False
            )
        return output

class CienaSaosFileTransfer(BaseFileTransfer):
    """Ciena SAOS SCP File Transfer driver."""

    def __init__(
        self, ssh_conn, source_file, dest_file, file_system="", direction="put"
    ):
        if file_system == "":
            file_system = "/tmp/users/{}".format(ssh_conn.username)
        super(CienaSaosFileTransfer, self).__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
        )

    def remote_space_available(self, search_pattern=""):
        """Return space available on Ciena SAOS"""
        remote_cmd = "file vols"
        remote_output = self.ssh_ctl_chan.send_command_expect(remote_cmd)

        # Try to ensure parsing is correct:
        # Filesystem           1K-blocks      Used Available Use% Mounted on
        # var                       1024       528       496  52% /var
        remote_output = remote_output.strip()
        output_lines = remote_output.splitlines()

        # First line is the header; second is the actual file system info
        header_line = output_lines[0]
        filesystem_line = output_lines[1]

        if "Filesystem" not in header_line or "Avail" not in header_line.split()[3]:
            # Filesystem  1K-blocks  Used   Avail Capacity  Mounted on
            msg = "Parsing error, unexpected output from {}:\n{}".format(
                remote_cmd, remote_output
            )
            raise ValueError(msg)

        longest_match = (0, 0)
        for filesystem_line in output_lines[1:]:
            mounted_on = filesystem_line.split()[5]
            if (
                self.file_system.startswith(mounted_on)
                and len(mounted_on) > longest_match[0]
            ):
                longest_match = (len(mounted_on), filesystem_line.split()[3])
        space_available = longest_match[1]

        if not re.search(r"^\d+$", space_available):
            msg = "Parsing error, unexpected output from {}:\n{}".format(
                remote_cmd, remote_output
            )
            raise ValueError(msg)

        return int(space_available) * 1024

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == "put":
            if not remote_cmd:
                remote_cmd = "file ls {}{}".format(self.file_system, self.dest_file)
            remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
            search_string = r"{}{}".format(self.file_system, self.dest_file)
            if "ERROR" in remote_out:
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

        remote_file = "{}{}".format(self.file_system, remote_file)

        if not remote_cmd:
            remote_cmd = "file ls -l {}".format(remote_file)

        remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)

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

    def remote_md5(self, base_cmd="", remote_file=None):
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

        remote_md5_cmd = "{} {}{}".format(base_cmd, self.file_system, remote_file)

        self.ssh_ctl_chan._enter_shell()
        dest_md5 = self.ssh_ctl_chan.send_command(
            remote_md5_cmd, expect_string=r"[\$#]", max_loops=1500
        )
        self.ssh_ctl_chan._return_cli()
        dest_md5 = self.process_md5(dest_md5, pattern=r"([0-9a-f]+)\s+")
        return dest_md5

    def enable_scp(self, cmd="system server scp enable"):
        return super(CienaSaosFileTransfer, self).enable_scp(cmd=cmd)

    def disable_scp(self, cmd="system server scp disable"):
        return super(CienaSaosFileTransfer, self).disable_scp(cmd=cmd)
    
    def scp_get_file(self, source_file, dest_file):
        #pass
        scp_cmd = "file scp "
        remote_cmd = "{} {} ".format(scp_cmd, source_file)
        return super(CienaSaosFileTransfer, self).scp_get_file(source_file=remote_cmd)
