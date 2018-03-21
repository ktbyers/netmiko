"""
Netmiko SCP operations.

Supports file get and file put operations.

SCP requires a separate SSH connection for a control channel.

Currently only supports Cisco IOS and Cisco ASA.
"""
from __future__ import print_function
from __future__ import unicode_literals

import re
import os
import hashlib

import scp


class SCPConn(object):
    """
    Establish a secure copy channel to the remote network device.

    Must close the SCP connection to get the file to write to the remote filesystem
    """
    def __init__(self, ssh_conn):
        self.ssh_ctl_chan = ssh_conn
        self.establish_scp_conn()

    def establish_scp_conn(self):
        """Establish the secure copy connection."""
        ssh_connect_params = self.ssh_ctl_chan._connect_params_dict()
        self.scp_conn = self.ssh_ctl_chan._build_ssh_client()
        self.scp_conn.connect(**ssh_connect_params)
        self.scp_client = scp.SCPClient(self.scp_conn.get_transport())

    def scp_transfer_file(self, source_file, dest_file):
        """Put file using SCP (for backwards compatibility)."""
        self.scp_client.put(source_file, dest_file)

    def scp_get_file(self, source_file, dest_file):
        """Get file using SCP."""
        self.scp_client.get(source_file, dest_file)

    def scp_put_file(self, source_file, dest_file):
        """Put file using SCP."""
        self.scp_client.put(source_file, dest_file)

    def close(self):
        """Close the SCP connection."""
        self.scp_conn.close()


class BaseFileTransfer(object):
    """Class to manage SCP file transfer and associated SSH control channel."""
    def __init__(self, ssh_conn, source_file, dest_file, file_system=None, direction='put'):
        self.ssh_ctl_chan = ssh_conn
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        auto_flag = 'cisco_ios' in ssh_conn.device_type or \
                    'cisco_xe' in ssh_conn.device_type or \
                    'cisco_xr' in ssh_conn.device_type
        if not file_system:
            if auto_flag:
                self.file_system = self.ssh_ctl_chan._autodetect_fs()
            else:
                raise ValueError("Destination file system not specified")
        else:
            self.file_system = file_system

        if direction == 'put':
            self.source_md5 = self.file_md5(source_file)
            self.file_size = os.stat(source_file).st_size
        elif direction == 'get':
            self.source_md5 = self.remote_md5(remote_file=source_file)
            self.file_size = self.remote_file_size(remote_file=source_file)
        else:
            raise ValueError("Invalid direction specified")

    def __enter__(self):
        """Context manager setup"""
        self.establish_scp_conn()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager cleanup."""
        self.close_scp_chan()

    def establish_scp_conn(self):
        """Establish SCP connection."""
        self.scp_conn = SCPConn(self.ssh_ctl_chan)

    def close_scp_chan(self):
        """Close the SCP connection to the remote network device."""
        self.scp_conn.close()
        self.scp_conn = None

    def remote_space_available(self, search_pattern=r"(\d+) bytes free"):
        """Return space available on remote device."""
        remote_cmd = "dir {}".format(self.file_system)
        remote_output = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        match = re.search(search_pattern, remote_output)
        return int(match.group(1))

    def _remote_space_available_unix(self, search_pattern=""):
        """Return space available on *nix system (BSD/Linux)."""
        self.ssh_ctl_chan._enter_shell()
        remote_cmd = "/bin/df -k {}".format(self.file_system)
        remote_output = self.ssh_ctl_chan.send_command(remote_cmd, expect_string=r"[\$#]")

        # Try to ensure parsing is correct:
        # Filesystem  512-blocks  Used   Avail Capacity  Mounted on
        # /dev/bo0s3f    1264808 16376 1147248     1%    /cf/var
        remote_output = remote_output.strip()
        output_lines = remote_output.splitlines()

        # First line is the header; second is the actual file system info
        header_line = output_lines[0]
        filesystem_line = output_lines[1]

        if 'Filesystem' not in header_line or 'Avail' not in header_line.split()[3]:
            # Filesystem  512-blocks  Used   Avail Capacity  Mounted on
            msg = "Parsing error, unexpected output from {}:\n{}".format(remote_cmd,
                                                                         remote_output)
            raise ValueError(msg)

        space_available = filesystem_line.split()[3]
        if not re.search(r"^\d+$", space_available):
            msg = "Parsing error, unexpected output from {}:\n{}".format(remote_cmd,
                                                                         remote_output)
            raise ValueError(msg)

        self.ssh_ctl_chan._return_cli()
        return int(space_available) * 1024

    def local_space_available(self):
        """Return space available on local filesystem."""
        destination_stats = os.statvfs(".")
        return destination_stats.f_bsize * destination_stats.f_bavail

    def verify_space_available(self, search_pattern=r"(\d+) bytes free"):
        """Verify sufficient space is available on destination file system (return boolean)."""
        if self.direction == 'put':
            space_avail = self.remote_space_available(search_pattern=search_pattern)
        elif self.direction == 'get':
            space_avail = self.local_space_available()
        if space_avail > self.file_size:
            return True
        return False

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == 'put':
            if not remote_cmd:
                remote_cmd = "dir {}/{}".format(self.file_system, self.dest_file)
            remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
            search_string = r"Directory of .*{0}".format(self.dest_file)
            if 'Error opening' in remote_out or 'No such file or directory' in remote_out:
                return False
            elif re.search(search_string, remote_out, flags=re.DOTALL):
                return True
            else:
                raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == 'get':
            return os.path.exists(self.dest_file)

    def _check_file_exists_unix(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == 'put':
            self.ssh_ctl_chan._enter_shell()
            remote_cmd = "ls {}".format(self.file_system)
            remote_out = self.ssh_ctl_chan.send_command(remote_cmd, expect_string=r"[\$#]")
            self.ssh_ctl_chan._return_cli()
            return self.dest_file in remote_out
        elif self.direction == 'get':
            return os.path.exists(self.dest_file)

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == 'put':
                remote_file = self.dest_file
            elif self.direction == 'get':
                remote_file = self.source_file
        if not remote_cmd:
            remote_cmd = "dir {}/{}".format(self.file_system, remote_file)
        remote_out = self.ssh_ctl_chan.send_command(remote_cmd)
        # Strip out "Directory of flash:/filename line
        remote_out = re.split(r"Directory of .*", remote_out)
        remote_out = "".join(remote_out)
        # Match line containing file name
        escape_file_name = re.escape(remote_file)
        pattern = r".*({}).*".format(escape_file_name)
        match = re.search(pattern, remote_out)
        if match:
            line = match.group(0)
            # Format will be 26  -rw-   6738  Jul 30 2016 19:49:50 -07:00  filename
            file_size = line.split()[2]
        if 'Error opening' in remote_out or 'No such file or directory' in remote_out:
            raise IOError("Unable to find file on remote system")
        else:
            return int(file_size)

    def _remote_file_size_unix(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == 'put':
                remote_file = self.dest_file
            elif self.direction == 'get':
                remote_file = self.source_file
        remote_file = "{}/{}".format(self.file_system, remote_file)
        if not remote_cmd:
            remote_cmd = "ls -l {}".format(remote_file)

        self.ssh_ctl_chan._enter_shell()
        remote_out = self.ssh_ctl_chan.send_command(remote_cmd, expect_string=r"[\$#]")
        escape_file_name = re.escape(remote_file)
        pattern = r"^.* ({}).*$".format(escape_file_name)
        match = re.search(pattern, remote_out, flags=re.M)
        if match:
            # Format: -rw-r--r--  1 pyclass  wheel  12 Nov  5 19:07 /var/tmp/test3.txt
            line = match.group(0)
            file_size = line.split()[4]

        self.ssh_ctl_chan._return_cli()
        return int(file_size)

    def file_md5(self, file_name):
        """Compute MD5 hash of file."""
        with open(file_name, "rb") as f:
            file_contents = f.read()
            file_hash = hashlib.md5(file_contents).hexdigest()
        return file_hash

    @staticmethod
    def process_md5(md5_output, pattern=r"=\s+(\S+)"):
        """
        Process the string to retrieve the MD5 hash

        Output from Cisco IOS (ASA is similar)
        .MD5 of flash:file_name Done!
        verify /md5 (flash:file_name) = 410db2a7015eaa42b1fe71f1bf3d59a2
        """
        match = re.search(pattern, md5_output)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid output from MD5 command: {}".format(md5_output))

    def compare_md5(self):
        """Compare md5 of file on network device to md5 of local file."""
        if self.direction == 'put':
            remote_md5 = self.remote_md5()
            return self.source_md5 == remote_md5
        elif self.direction == 'get':
            local_md5 = self.file_md5(self.dest_file)
            return self.source_md5 == local_md5

    def remote_md5(self, base_cmd='verify /md5', remote_file=None):
        """Calculate remote MD5 and returns the hash.

        This command can be CPU intensive on the remote device.
        """
        if remote_file is None:
            if self.direction == 'put':
                remote_file = self.dest_file
            elif self.direction == 'get':
                remote_file = self.source_file
        remote_md5_cmd = "{} {}/{}".format(base_cmd, self.file_system, remote_file)
        dest_md5 = self.ssh_ctl_chan.send_command(remote_md5_cmd, max_loops=1500)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    def transfer_file(self):
        """SCP transfer file."""
        if self.direction == 'put':
            self.put_file()
        elif self.direction == 'get':
            self.get_file()

    def get_file(self):
        """SCP copy the file from the remote device to local system."""
        source_file = "{}/{}".format(self.file_system, self.source_file)
        self.scp_conn.scp_get_file(source_file, self.dest_file)
        self.scp_conn.close()

    def put_file(self):
        """SCP copy the file from the local system to the remote device."""
        destination = "{}/{}".format(self.file_system, self.dest_file)
        self.scp_conn.scp_transfer_file(self.source_file, destination)
        # Must close the SCP connection to get the file written (flush)
        self.scp_conn.close()

    def verify_file(self):
        """Verify the file has been transferred correctly."""
        return self.compare_md5()

    def enable_scp(self, cmd=None):
        """
        Enable SCP on remote device.

        Defaults to Cisco IOS command
        """
        if cmd is None:
            cmd = ['ip scp server enable']
        elif not hasattr(cmd, '__iter__'):
            cmd = [cmd]
        self.ssh_ctl_chan.send_config_set(cmd)

    def disable_scp(self, cmd=None):
        """
        Disable SCP on remote device.

        Defaults to Cisco IOS command
        """
        if cmd is None:
            cmd = ['no ip scp server enable']
        elif not hasattr(cmd, '__iter__'):
            cmd = [cmd]
        self.ssh_ctl_chan.send_config_set(cmd)
