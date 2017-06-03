"""Aruba OS support"""
from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection
from datetime import date
import time
import socket
import re

from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.ssh_exception import NetMikoTimeoutException


class ArubaSSH(CiscoSSHConnection):
    """Aruba OS support"""
    def session_preparation(self):
        """Aruba OS requires enable mode to disable paging."""
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(1 * delay_factor)
        self._test_channel_read()
        self.set_base_prompt()
        self.enable()
        self.disable_paging(command="no paging")

    def check_config_mode(self, check_string='(config) #', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Aruba uses "(<controller name>) (config) #" as config prompt
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super(ArubaSSH, self).check_config_mode(check_string=check_string,
                                                       pattern=pattern)

    def backup(self, username, pwd, server, protocol="ftp",  path=".", timeout=30):
        """
        Creates a backup and then transfers it through the preferred protocol ftp, scp or tftp.
        The filename where that is uploaded has the format "yearmonthday.hostname.tar.gz"
        :param username: username used to upload the backup
        :param pwd: password upload the backup
        :param server: ip address of the remote server
        :param protocol: ftp, scp or tftp. Default if ftp
        :param path: path where the backup is going to be uploaded, default is "."
        :param timeout: time that the script waits for prompt after the backup has been sent.
        When the server it's not reachable it takes up to 25 seconds to timeout, that's why
        such high time timeout is needed
        :return: True or False in case the
        The command to send the backup has the format "copy origin filename protocol IP
        (username path) dest_file_name
        """
        debug = False
        # '\r' is needed for the controller to recognize the end of the password so we attach it
        pwd += '\r'
        today = date.today()
        username_protocols = ['ftp', 'scp']
        no_username_protocol = ['tftp']
        protocol = protocol.lower()

        # Filename formatting
        filename = "%s%s%s.%s.tar.gz" % (today.year, today.month, today.day, self.host)

        # Copy backup formatting depending on protocol
        if protocol in username_protocols:
            send_backup = "copy flash: flashbackup.tar.gz %s: %s %s %s %s" % (
            protocol, server, username, path, filename)
            expect = "Password:"
        elif protocol in no_username_protocol:
            send_backup = "copy flash: flashbackup.tar.gz %s: %s %s " % (protocol, server, filename)
            expect = ""
        else:
            raise ValueError("Protocol %s is not an available option" % protocol)

        # Backup is created
        create_backup = "backup flash"
        output = self.send_command(command_string=create_backup)

        # Backup is sent through defined protocol
        output += self.send_command(command_string=send_backup, expect_string=expect)
        self.write_channel(pwd)

        # It waits for prompt until timeout is reached
        output += self._read_channel_expect_timing(timeout=timeout)

        if debug:
            print output

        for value in output.split('\n'):
            if re.search('Error', value):
                raise ValueError("An error showed up in the process: %s" % value)

        return True

    def _read_channel_expect_timing(self, pattern='', re_flags=0, timeout=1):
        """
        Function that reads channel until pattern is detected.

        pattern takes a regular expression.

        By default pattern will be self.base_prompt

        Note: this currently reads beyond pattern. In the case of SSH it reads MAX_BUFFER.
        In the case of telnet it reads all non-blocking data.

        There are dependecies here like determining whether in config_mode that are actually
        depending on reading beyond pattern.
        """
        debug = False
        output = ''
        if not pattern:
            pattern = self.base_prompt
        pattern = re.escape(pattern)
        if debug:
            print("Pattern is: {}".format(pattern))

        # Will loop for self.timeout time (unless modified by global_delay_factor)
        i = 1
        loop_delay = .1
        max_loops = timeout / loop_delay
        while i < max_loops:
            if self.protocol == 'ssh':
                try:
                    # If no data available will wait timeout seconds trying to read
                    output += self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                except socket.timeout:
                    raise NetMikoTimeoutException("Timed-out reading channel, data not available.")
            elif self.protocol == 'telnet':
                output += self.read_channel()
            if re.search(pattern, output, flags=re_flags):
                if debug:
                    print("Pattern found: {} {}".format(pattern, output))
                return output
            time.sleep(loop_delay * self.global_delay_factor)
            i += 1
        raise NetMikoTimeoutException("Timed-out reading channel, pattern not found in output: {}"
                                      .format(pattern))