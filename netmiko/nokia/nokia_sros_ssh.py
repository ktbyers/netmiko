#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 - 2019 Kirk Byers
# Copyright (c) 2014 - 2019 Twin Bridges Technology
# Copyright (c) 2019 NOKIA Inc.
# MIT License - See License file at:
#   https://github.com/ktbyers/netmiko/blob/develop/LICENSE

import re
import os
import time

from netmiko import log
from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer


class NokiaSrosSSH(BaseConnection):
    """
    Implement methods for interacting with Nokia SR OS devices.

    Not applicable in Nokia SR OS (disabled):
        - enable()
        - exit_enable_mode()
        - check_enable_mode()

    Overriden methods to adapt Nokia SR OS behavior (changed):
        - session_preparation()
        - set_base_prompt()
        - config_mode()
        - exit_config_mode()
        - check_config_mode()
        - save_config()
        - commit()
        - strip_prompt()
    """

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        if "@" in self.base_prompt:
            self.disable_paging(command="environment more false")
            self.set_terminal_width(command="environment console width 512")
        else:
            self.disable_paging(command="environment no more")

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args, **kwargs):
        """Remove the > when navigating into the different config level."""
        cur_base_prompt = super().set_base_prompt(*args, **kwargs)
        match = re.search(r"\*?(.*)(>.*)*#", cur_base_prompt)
        if match:

            # strip off >... from base_prompt

            self.base_prompt = match.group(1)
            return self.base_prompt

    def enable(self, *args, **kwargs):
        """Nokia SR OS does not support enable-mode"""
        pass

    def check_enable_mode(self, *args, **kwargs):
        """Nokia SR OS does not support enable-mode"""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """Nokia SR OS does not support enable-mode"""
        pass

    def config_mode(self, *args, **kwargs):
        """Enable config edit-mode for Nokia SR OS"""
        self.write_channel(self.RETURN)
        output = self.read_until_prompt()
        if "@" in self.base_prompt:
            if "(ex)[" not in output:
                self.write_channel(self.normalize_cmd("edit-config exclusive"))
                output += self.read_until_prompt()
            else:
                log.warning("Already in config edit-mode!")
        return output

    def exit_config_mode(self, *args, **kwargs):
        """Disable config edit-mode for Nokia SR OS"""
        self.write_channel(self.normalize_cmd("exit all"))
        output = self.read_until_prompt()
        if "@" in self.base_prompt:
            if "(ex)[" in output:
                if "*(ex)[" in output:
                    log.warning("Uncommitted changes! Need to discard!")
                    self.write_channel(self.normalize_cmd("discard"))
                    output += self.read_until_prompt()
                self.write_channel(self.normalize_cmd("quit-config"))
                output += self.read_until_prompt()
            else:
                log.warning("Already in operational mode!")
        return output

    def check_config_mode(self, *args, **kwargs):
        """Check config edit-mode for Nokia SR OS"""
        if "@" not in self.base_prompt:
            return True
        else:
            self.write_channel(self.RETURN)
            output = self.read_until_prompt()
            return "(ex)[" in output

    def save_config(self, *args, **kwargs):
        """Persist configuration to cflash for Nokia SR OS"""
        output = self.send_command(command_string="/admin save")
        return output

    def commit(self, *args, **kwargs):
        """Activate changes from private candidate for Nokia SR OS"""
        self.write_channel(self.normalize_cmd("exit all"))
        output = self.read_until_prompt()
        if "@" in self.base_prompt:
            if "(ex)[" in output:
                if "*(ex)[" in output:
                    log.info("Apply uncommitted changes!")
                    self.write_channel(self.normalize_cmd("commit"))
                    output += self.read_until_prompt()
            else:
                log.warning("Commit is only supported in config edit-mode")
        else:
            log.warning("Commit is only supported in MD-CLI")
        return output

    def _discard(self):
        """Discard changes from private candidate for Nokia SR OS"""
        self.write_channel(self.normalize_cmd("exit all"))
        output = self.read_until_prompt()
        if "@" in self.base_prompt:
            if "(ex)[" in output:
                if "*(ex)[" in output:
                    log.info("Discard uncommitted changes!")
                    self.write_channel(self.normalize_cmd("discard"))
                    output += self.read_until_prompt()
            else:
                log.warning("Discard is only supported in config edit-mode")
        else:
            log.warning("Discard is only supported in MD-CLI")
        return output

    def strip_prompt(self, *args, **kwargs):
        """Strip prompt from the output."""
        output = super().strip_prompt(*args, **kwargs)
        if "@" in self.base_prompt:
            # Remove context prompt too
            strips = r"[\r\n]*\!?\*?(\((ex|gl|pr|ro)\))?\[\S*\][\r\n]*"
            return re.sub(strips, "", output)
        else:
            return output


class NokiaSrosFileTransfer(BaseFileTransfer):
    def __init__(self, ssh_conn, source_file, dest_file, file_system, direction="put"):

        self.ssh_ctl_chan = ssh_conn
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        if not file_system:
            self.file_system = "cf3:"
        else:
            self.file_system = file_system

        if direction == "put":
            self.file_size = os.stat(source_file).st_size
        elif direction == "get":
            self.file_size = self.remote_file_size(remote_file=source_file)
        else:
            raise ValueError("Invalid direction specified")

    def remote_space_available(self, search_pattern=r"(\d+) \w+ free"):
        """Return space available on remote device."""
        remote_cmd = "file dir {}".format(self.file_system)
        remote_output = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        match = re.search(search_pattern, remote_output)
        return int(match.group(1))

    def check_file_exists(self, remote_cmd=""):
        """Check if destination file exists (returns boolean)."""
        if self.direction == "put":
            remote_cmd = "file dir {}/{}".format(self.file_system, self.dest_file)
            remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
            if "File Not Found" in remote_out:
                return False
            elif self.dest_file in remote_out:
                return True
            else:
                raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == "get":
            return os.path.exists(self.dest_file)

    def remote_file_size(self, remote_cmd=None, remote_file=None):
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        if not remote_cmd:
            remote_cmd = "file dir {}/{}".format(self.file_system, remote_file)
        remote_out = self.ssh_ctl_chan.send_command(remote_cmd)

        if "File Not Found" in remote_out:
            raise IOError("Unable to find file on remote system")

        # Parse dir output for filename. Output format is:
        # "10/16/2019  10:00p                6738 {filename}"
        pattern = r"(\S+)[ \t]+(\S+)[ \t]+(\d+)[ \t]+{}".format(re.escape(remote_file))
        match = re.search(pattern, remote_out)

        if not match:
            raise ValueError("Filename entry not found in dir output")

        file_size = int(match.group(3))
        return file_size

    def remote_md5(self, base_cmd=None, remote_file=None):
        """Nokia SR OS does not expose a md5sum method"""
        raise NotImplementedError

    def compare_md5(self):
        """Nokia SR OS does not expose a md5sum method"""
        raise NotImplementedError

    def verify_file(self):
        """Verify the file has been transferred correctly based on filesize."""
        if self.direction == "put":
            return self.file_size == self.remote_file_size(remote_file=self.source_file)
        elif self.direction == "get":
            return self.file_size == os.stat(self.source_file).st_size
