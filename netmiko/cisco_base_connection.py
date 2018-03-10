"""CiscoBaseConnection is netmiko SSH class for Cisco and Cisco-like platforms."""
from __future__ import unicode_literals
from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer
from netmiko.ssh_exception import NetMikoAuthenticationException
import re
import time


class CiscoBaseConnection(BaseConnection):
    """Base Class for cisco-like behavior."""
    def check_enable_mode(self, check_string='#'):
        """Check if in enable mode. Return boolean."""
        return super(CiscoBaseConnection, self).check_enable_mode(check_string=check_string)

    def enable(self, cmd='enable', pattern='ssword', re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super(CiscoBaseConnection, self).enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command='disable'):
        """Exits enable (privileged exec) mode."""
        return super(CiscoBaseConnection, self).exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=')#', pattern=''):
        """
        Checks if the device is in configuration mode or not.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        return super(CiscoBaseConnection, self).check_config_mode(check_string=check_string,
                                                                  pattern=pattern)

    def config_mode(self, config_command='config term', pattern=''):
        """
        Enter into configuration mode on remote device.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super(CiscoBaseConnection, self).config_mode(config_command=config_command,
                                                            pattern=pattern)

    def exit_config_mode(self, exit_config='end', pattern=''):
        """Exit from configuration mode."""
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super(CiscoBaseConnection, self).exit_config_mode(exit_config=exit_config,
                                                                 pattern=pattern)

    def serial_login(self, pri_prompt_terminator=r'#\s*$', alt_prompt_terminator=r'>\s*$',
                     username_pattern=r"(?:[Uu]ser:|sername|ogin)", pwd_pattern=r"assword",
                     delay_factor=1, max_loops=20):
        self.write_channel(self.TELNET_RETURN)
        output = self.read_channel()
        if (re.search(pri_prompt_terminator, output, flags=re.M)
                or re.search(alt_prompt_terminator, output, flags=re.M)):
            return output
        else:
            return self.telnet_login(pri_prompt_terminator, alt_prompt_terminator,
                                     username_pattern, pwd_pattern, delay_factor, max_loops)

    def telnet_login(self, pri_prompt_terminator=r'#\s*$', alt_prompt_terminator=r'>\s*$',
                     username_pattern=r"(?:[Uu]ser:|sername|ogin|User Name)",
                     pwd_pattern=r"assword",
                     delay_factor=1, max_loops=20):
        """Telnet login. Can be username/password or just password."""
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)

        output = ''
        return_msg = ''
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output

                # Search for username pattern / send username
                if re.search(username_pattern, output):
                    self.write_channel(self.username + self.TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for password pattern / send password
                if re.search(pwd_pattern, output):
                    self.write_channel(self.password + self.TELNET_RETURN)
                    time.sleep(.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if (re.search(pri_prompt_terminator, output, flags=re.M)
                            or re.search(alt_prompt_terminator, output, flags=re.M)):
                        return return_msg

                # Support direct telnet through terminal server
                if re.search(r"initial configuration dialog\? \[yes/no\]: ", output):
                    self.write_channel("no" + self.TELNET_RETURN)
                    time.sleep(.5 * delay_factor)
                    count = 0
                    while count < 15:
                        output = self.read_channel()
                        return_msg += output
                        if re.search(r"ress RETURN to get started", output):
                            output = ""
                            break
                        time.sleep(2 * delay_factor)
                        count += 1

                # Check for device with no password configured
                if re.search(r"assword required, but none set", output):
                    msg = "Telnet login failed - Password required, but none set: {}".format(
                        self.host)
                    raise NetMikoAuthenticationException(msg)

                # Check if proper data received
                if (re.search(pri_prompt_terminator, output, flags=re.M)
                        or re.search(alt_prompt_terminator, output, flags=re.M)):
                    return return_msg

                self.write_channel(self.TELNET_RETURN)
                time.sleep(.5 * delay_factor)
                i += 1
            except EOFError:
                msg = "Telnet login failed: {}".format(self.host)
                raise NetMikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if (re.search(pri_prompt_terminator, output, flags=re.M)
                or re.search(alt_prompt_terminator, output, flags=re.M)):
            return return_msg

        msg = "Telnet login failed: {}".format(self.host)
        raise NetMikoAuthenticationException(msg)

    def cleanup(self):
        """Gracefully exit the SSH session."""
        try:
            self.exit_config_mode()
        except Exception:
            # Always try to send 'exit' regardless of whether exit_config_mode works or not.
            pass
        self.write_channel("exit" + self.RETURN)

    def _autodetect_fs(self, cmd='dir', pattern=r'Directory of (.*)/'):
        """Autodetect the file system on the remote device. Used by SCP operations."""
        if not self.check_enable_mode():
            raise ValueError('Must be in enable mode to auto-detect the file-system.')
        output = self.send_command_expect(cmd)
        match = re.search(pattern, output)
        if match:
            file_system = match.group(1)
            # Test file_system
            cmd = "dir {}".format(file_system)
            output = self.send_command_expect(cmd)
            if '% Invalid' in output or '%Error:' in output:
                raise ValueError("An error occurred in dynamically determining remote file "
                                 "system: {} {}".format(cmd, output))
            else:
                return file_system

        raise ValueError("An error occurred in dynamically determining remote file "
                         "system: {} {}".format(cmd, output))

    def save_config(self, cmd='copy running-config startup-config', confirm=False,
                    confirm_response=''):
        """Saves Config."""
        self.enable()
        if confirm:
            output = self.send_command_timing(command_string=cmd)
            if confirm_response:
                output += self.send_command_timing(confirm_response)
            else:
                # Send enter by default
                output += self.send_command_timing(self.RETURN)
        else:
            # Some devices are slow so match on trailing-prompt if you can
            output = self.send_command(command_string=cmd)
        return output


class CiscoSSHConnection(CiscoBaseConnection):
    pass


class CiscoFileTransfer(BaseFileTransfer):
    pass
