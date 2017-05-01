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
import time
import io

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


class FileTransfer(object):
    """Class to manage SCP file transfer and associated SSH control channel."""
    def __init__(self, ssh_conn, source_file, dest_file, file_system=None, direction='put'):
        self.ssh_ctl_chan = ssh_conn
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        if not file_system:
            self.file_system = self.ssh_ctl_chan._autodetect_fs()
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
        if exc_type is not None:
            raise exc_type(exc_value)

    def establish_scp_conn(self):
        """Establish SCP connection."""
        self.scp_conn = SCPConn(self.ssh_ctl_chan)

    def close_scp_chan(self):
        """Close the SCP connection to the remote network device."""
        self.scp_conn.close()
        self.scp_conn = None

    def remote_space_available(self, search_pattern=r"bytes total \((.*) bytes free\)"):
        """Return space available on remote device."""
        remote_cmd = "dir {0}".format(self.file_system)
        remote_output = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        match = re.search(search_pattern, remote_output)
        return int(match.group(1))

    def local_space_available(self):
        """Return space available on local filesystem."""
        destination_stats = os.statvfs(".")
        return destination_stats.f_bsize * destination_stats.f_bavail

    def verify_space_available(self, search_pattern=r"bytes total \((.*) bytes free\)"):
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
                remote_cmd = "dir {0}/{1}".format(self.file_system, self.dest_file)
            remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
            search_string = r"Directory of .*{0}".format(self.dest_file)
            if 'Error opening' in remote_out:
                return False
            elif re.search(search_string, remote_out):
                return True
            else:
                raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == 'get':
            return os.path.exists(self.dest_file)

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        if remote_file is None:
            remote_file = self.dest_file
        if not remote_cmd:
            remote_cmd = "dir {0}/{1}".format(self.file_system, remote_file)
        remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        # Strip out "Directory of flash:/filename line
        remote_out = re.split(r"Directory of .*", remote_out)
        remote_out = "".join(remote_out)
        # Match line containing file name
        escape_file_name = re.escape(remote_file)
        pattern = r".*({0}).*".format(escape_file_name)
        match = re.search(pattern, remote_out)
        if match:
            line = match.group(0)
            # Format will be 26  -rw-   6738  Jul 30 2016 19:49:50 -07:00  filename
            file_size = line.split()[2]
        if 'Error opening' in remote_out:
            raise IOError("Unable to find file on remote system")
        else:
            return int(file_size)

    def file_md5(self, file_name):
        """Compute MD5 hash of file."""
        with open(file_name, "rb") as f:
            file_contents = f.read()
            file_hash = hashlib.md5(file_contents).hexdigest()
        return file_hash

    @staticmethod
    def process_md5(md5_output, pattern=r"= (.*)"):
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
            raise ValueError("Invalid output from MD5 command: {0}".format(md5_output))

    def compare_md5(self, base_cmd='verify /md5'):
        """Compare md5 of file on network device to md5 of local file"""
        if self.direction == 'put':
            remote_md5 = self.remote_md5(base_cmd=base_cmd)
            return self.source_md5 == remote_md5
        elif self.direction == 'get':
            local_md5 = self.file_md5(self.dest_file)
            return self.source_md5 == local_md5

    def remote_md5(self, base_cmd='verify /md5', remote_file=None):
        """
        Calculate remote MD5 and return the checksum.

        This command can be CPU intensive on the remote device.
        """
        if remote_file is None:
            remote_file = self.dest_file
        remote_md5_cmd = "{0} {1}{2}".format(base_cmd, self.file_system, remote_file)
        dest_md5 = self.ssh_ctl_chan.send_command_expect(remote_md5_cmd, delay_factor=3.0)
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
        self.scp_conn.scp_get_file(self.source_file, self.dest_file)
        self.scp_conn.close()

    def put_file(self):
        """SCP copy the file from the local system to the remote device."""
        destination = "{0}{1}".format(self.file_system, self.dest_file)
        if ':' not in destination:
            raise ValueError("Invalid destination file system specified")
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


class InLineTransfer(FileTransfer):
    """Use TCL on Cisco IOS to directly transfer file."""
    def __init__(self, ssh_conn, source_file=None, dest_file=None, file_system=None,
                 direction='put', source_config=None):
        if source_file and source_config:
            msg = "Invalid call to InLineTransfer both source_file and source_config specified."
            raise ValueError(msg)
        if direction != 'put':
            raise ValueError("Only put operation supported by InLineTransfer.")

        self.ssh_ctl_chan = ssh_conn
        if source_file:
            self.source_file = source_file
            self.source_config = None
            self.source_md5 = self.file_md5(source_file)
            self.file_size = os.stat(source_file).st_size
        elif source_config:
            self.source_file = None
            self.source_config = source_config
            self.source_md5 = self.config_md5(source_config)
            self.file_size = len(source_config.encode('UTF-8'))
        self.dest_file = dest_file
        self.direction = direction

        if not file_system:
            self.file_system = self.ssh_ctl_chan._autodetect_fs()
        else:
            self.file_system = file_system

    @staticmethod
    def _read_file(file_name):
        with io.open(file_name, "rt", encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _tcl_newline_rationalize(tcl_string):
        """
        When using put inside a TCL {} section the newline is considered a new TCL
        statement and causes a missing curly-brace message. Convert "\n" to "\r". TCL
        will convert the "\r" to a "\n" i.e. you will see a "\n" inside the file on the
        Cisco IOS device.
        """
        NEWLINE = r"\n"
        CARRIAGE_RETURN = r"\r"
        tmp_string = re.sub(NEWLINE, CARRIAGE_RETURN, tcl_string)
        if re.search(r"[{}]", tmp_string):
            msg = "Curly brace detected in string; TCL requires this be escaped."
            raise ValueError(msg)
        return tmp_string

    def __enter__(self):
        self._enter_tcl_mode()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _ = self._exit_tcl_mode()  # noqa
        if exc_type is not None:
            raise exc_type(exc_value)

    def _enter_tcl_mode(self):
        TCL_ENTER = 'tclsh'
        cmd_failed = ['Translating "tclsh"', '% Unknown command', '% Bad IP address']
        output = self.ssh_ctl_chan.send_command(TCL_ENTER, expect_string=r"\(tcl\)#",
                                                strip_prompt=False, strip_command=False)
        for pattern in cmd_failed:
            if pattern in output:
                raise ValueError("Failed to enter tclsh mode on router: {}".format(output))
        return output

    def _exit_tcl_mode(self):
        TCL_EXIT = 'tclquit'
        self.ssh_ctl_chan.write_channel("\r")
        time.sleep(1)
        output = self.ssh_ctl_chan.read_channel()
        if '(tcl)' in output:
            self.ssh_ctl_chan.write_channel(TCL_EXIT + "\r")
        time.sleep(1)
        output += self.ssh_ctl_chan.read_channel()
        return output

    def establish_scp_conn(self):
        raise NotImplementedError

    def close_scp_chan(self):
        raise NotImplementedError

    def local_space_available(self):
        raise NotImplementedError

    def file_md5(self, file_name):
        """Compute MD5 hash of file."""
        file_contents = self._read_file(file_name)
        file_contents = file_contents + '\n'    # Cisco IOS automatically adds this
        file_contents = file_contents.encode('UTF-8')
        return hashlib.md5(file_contents).hexdigest()

    def config_md5(self, source_config):
        """Compute MD5 hash of file."""
        file_contents = source_config + '\n'    # Cisco IOS automatically adds this
        file_contents = file_contents.encode('UTF-8')
        return hashlib.md5(file_contents).hexdigest()

    def put_file(self):
        curlybrace = r'{'
        TCL_FILECMD_ENTER = 'puts [open "{}{}" w+] {}'.format(self.file_system,
                                                              self.dest_file, curlybrace)
        TCL_FILECMD_EXIT = '}'

        if self.source_file:
            file_contents = self._read_file(self.source_file)
        elif self.source_config:
            file_contents = self.source_config
        file_contents = self._tcl_newline_rationalize(file_contents)

        # Try to remove any existing data
        self.ssh_ctl_chan.clear_buffer()

        self.ssh_ctl_chan.write_channel(TCL_FILECMD_ENTER)
        time.sleep(.25)
        self.ssh_ctl_chan.write_channel(file_contents)
        self.ssh_ctl_chan.write_channel(TCL_FILECMD_EXIT + "\r")

        # This operation can be slow (depends on the size of the file)
        max_loops = 400
        sleep_time = 4
        if self.file_size >= 2500:
            max_loops = 1500
            sleep_time = 12
        elif self.file_size >= 7500:
            max_loops = 3000
            sleep_time = 25

        # Initial delay
        time.sleep(sleep_time)

        # File paste and TCL_FILECMD_exit should be indicated by "router(tcl)#"
        output = self.ssh_ctl_chan._read_channel_expect(pattern=r"\(tcl\)", max_loops=max_loops)

        # The file doesn't write until tclquit
        TCL_EXIT = 'tclquit'
        self.ssh_ctl_chan.write_channel(TCL_EXIT + "\r")

        time.sleep(1)
        # Read all data remaining from the TCLSH session
        output += self.ssh_ctl_chan._read_channel_expect(max_loops=max_loops)
        return output

    def get_file(self):
        raise NotImplementedError

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
