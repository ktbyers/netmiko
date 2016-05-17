"""SSHConnection is netmiko SSH class for Cisco and Cisco-like platforms."""
from __future__ import unicode_literals
from netmiko.base_connection import BaseSSHConnection
import re


class SSHConnection(BaseSSHConnection):
    """Based upon Cisco CLI behavior."""
    def check_enable_mode(self, check_string='#'):
        """Check if in enable mode. Return boolean."""
        return super(SSHConnection, self).check_enable_mode(check_string=check_string)

    def enable(self, cmd='enable', pattern='password', re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super(SSHConnection, self).enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command='disable'):
        """Exits enable (privileged exec) mode."""
        return super(SSHConnection, self).exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=')#', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            pattern = self.base_prompt[:16]
        return super(SSHConnection, self).check_config_mode(check_string=check_string,
                                                            pattern=pattern)

    def config_mode(self, config_command='config term', pattern=''):
        """
        Enter into configuration mode on remote device.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            pattern = self.base_prompt[:16]
        return super(SSHConnection, self).config_mode(config_command=config_command,
                                                      pattern=pattern)

    def exit_config_mode(self, exit_config='end', pattern=''):
        """Exit from configuration mode."""
        if not pattern:
            pattern = self.base_prompt[:16]
        return super(SSHConnection, self).exit_config_mode(exit_config=exit_config,
                                                           pattern=pattern)

    def cleanup(self):
        """Gracefully exit the SSH session."""
        self.exit_config_mode()
        self.remote_conn.sendall("exit\n")

    def _autodetect_fs(self, cmd='dir', pattern=r'Directory of (.*)/'):
        """Autodetect the file system on the remote device. Used by SCP operations."""
        output = self.send_command_expect(cmd)
        match = re.search(pattern, output)
        if match:
            file_system = match.group(1)
            # Test file_system
            cmd = "dir {}".format(file_system)
            output = self.send_command_expect(cmd)
            if '% Invalid' not in output:
                return file_system

        raise ValueError("An error occurred in dynamically determining remote file "
                         "system: {} {}".format(cmd, output))
