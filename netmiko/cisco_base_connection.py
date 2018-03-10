"""CiscoBaseConnection is netmiko SSH class for Cisco and Cisco-like platforms."""
from __future__ import unicode_literals
from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer
from netmiko.ssh_exception import NetMikoAuthenticationException
import re
import time


class CiscoBaseConnection(BaseConnection):
    """Base Class for cisco-like behavior."""
    def check_enable_mode(self, check_string='#', newline_format='\n'):
        """Check if in enable mode. Return boolean."""
        return super(CiscoBaseConnection, self).check_enable_mode(check_string=check_string,
                                                                  newline_format=newline_format)

    def enable(self, cmd='enable', pattern='ssword', re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super(CiscoBaseConnection, self).enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command='disable'):
        """Exits enable (privileged exec) mode."""
        return super(CiscoBaseConnection, self).exit_enable_mode(exit_command=exit_command)

    def check_config_mode(self, check_string=')#', pattern='', newline_format='\n'):
        """
        Checks if the device is in configuration mode or not.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            #pattern = self.base_prompt[:16]
            pattern = self.base_prompt[:14]
        return super(CiscoBaseConnection, self).check_config_mode(check_string=check_string,
                                                                  pattern=pattern,
                                                                  newline_format=newline_format)

    def config_mode(self, config_command='config term', pattern=''):
        """
        Enter into configuration mode on remote device.

        Cisco IOS devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            #pattern = self.base_prompt[:16]
            #pattern = self.current_prompt[:16]
            pattern = self.base_prompt[:14]
            pattern = self.current_prompt[:14]
        return super(CiscoBaseConnection, self).config_mode(config_command=config_command,
                                                            pattern=pattern)

    def exit_config_mode(self, exit_config='end', pattern=''):
        """Exit from configuration mode."""
        if not pattern:
            #pattern = self.base_prompt[:16]
            #pattern = self.current_prompt[:16]
            pattern = self.base_prompt[:14]
            pattern = self.current_prompt[:14]
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
                     username_pattern=r"(?:[Uu]ser:|sername|ogin|User Name)", pwd_pattern=r"(assword)|(ecret)",
                     delay_factor=1, delay_factor2=30, max_loops=60):
        """Telnet login. Can be username/password or just password."""
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)

        delay_factor2 = self.select_delay_factor(delay_factor2)

        output = ''
        return_msg = ''
        i = 1

        is_spitfire = False

        #import pdb; pdb.set_trace()
        while i <= max_loops:
            try:
                output = self.read_channel(verbose=True)
                #This below if block is addeed because when the telnet console starts with UserName,
                #self.read_channel which internally calls telnetlib.read_ver_eager() returns empty string
                #So, assign it to self.find_prompt()
                if output == '':
                    output=self.find_prompt()
                print (output)
                return_msg += output

                #is at spitfire xr prompt
                if re.search('xr#', output):
                    return return_msg

                #At Rebooted BMC prompt
                # reboot_bmc_to_bmc_cmd = 'boot'
                rebooted_bmc_prompt_pattern = r"cisco-bmc#"
                if re.search(rebooted_bmc_prompt_pattern, output):
                    self.write_channel(TELNET_RETURN + "boot" + TELNET_RETURN)
                    time.sleep(2 * delay_factor2)
                    self.write_channel(TELNET_RETURN)
                    output = self.read_channel(verbose=True)
                    return_msg += output

                #At BMC prompt
                bmc_prompt_pattern = r"root@spitfire-arm:~#"
                if re.search(bmc_prompt_pattern, output):
                    self.write_channel(TELNET_RETURN + "\x17" + TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel(verbose=True)
                    return_msg += output


                # Search for linux host prompt pattern [xr:~] or x86 prompt pattern
                linux_prompt_pattern = r"\[xr:~]\$"
                switch_to_xr_command = 'xr'
                x86_prompt_pattern = r"root@xr:~#"
                if re.search(linux_prompt_pattern, output) or re.search(x86_prompt_pattern, output):
                    self.write_channel(TELNET_RETURN + "xr" + TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel(verbose=True)
                    return_msg += output

                # If previously from xr prompt, if bash was executed to go to linux host prompt,
                # then inorder to go back to xr prompt, no need of xrlogin and password,
                # just do "exit" cmd
                xr_no_login_pattern = "Exec cannot be started from within an existing exec session"
                if re.search(xr_no_login_pattern, output):
                    self.write_channel(TELNET_RETURN + "exit" + TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel(verbose=True)
                    return_msg += output
                    if pri_prompt_terminator in output or alt_prompt_terminator in output:
                        return return_msg
                #import pdb; pdb.set_trace()

                # If previously from xr prompt, XR not started, must restart XR
                xr_not_started = r"(error while loading shared libraries)|(cannot open shared object)"
                if re.search(xr_not_started, output):
                    self.write_channel("initctl start ios-xr.routing.start" + TELNET_RETURN)
                    time.sleep(2 * delay_factor2)
                    self.write_channel(TELNET_RETURN)
                    output = self.read_channel(verbose=True)
                    return_msg += output


                # Search for standby console pattern
                standby_pattern=r"RP Node is not ready or active for login"
                if re.search(standby_pattern,output):
                    ''' Session is standby state '''
                    return return_msg

                my_password = self.password
                # Search for username pattern / send username OR
                # If the prompt shows "xr login:", the you can directly login to xr using xr username
                # and password or you can login to linux host, using linux host's username password
                if re.search(username_pattern, output):
                    bmc_login_pattern = "spitfire-arm login:"
                    if re.search(bmc_login_pattern, output):
                        my_password = '0penBmc'
                    else:
                        my_password = self.password

                    time.sleep(1)
                    self.write_channel(self.username + self.TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel(verbose=True)
                    return_msg += output

                else:
                    xr_or_host_login_pattern = "xr login:"
                    if re.search(xr_or_host_login_pattern, output):
                        self.write_channel(self.username + TELNET_RETURN)
                        time.sleep(1 * delay_factor)
                        output = self.read_channel(verbose=True)
                        print ('output after passing username = ', output)
                        return_msg += output

                # Search for password pattern / send password
                if re.search(pwd_pattern, output):
                    self.write_channel(self.password + self.TELNET_RETURN)
                    time.sleep(.5 * delay_factor)
                    output = self.read_channel(verbose=True)
                    return_msg += output
                    if (pri_prompt_terminator in output or alt_prompt_terminator in output) and not re.search(x86_prompt_pattern, output):
                        return return_msg
                    if re.search(pwd_pattern, output):
                        self.write_channel(my_password + TELNET_RETURN)
                        time.sleep(.5 * delay_factor)
                        output = self.read_channel(verbose=True)
                        return_msg += output
                # Search for standby console pattern
                standby_pattern=r"RP Node is not ready or active for login"
                if re.search(standby_pattern,output):
                    ''' Session is standby state '''
                    return return_msg

                #Search for "VR0 con0/RP0/CPU0 is now available Press RETURN to get started" pattern
                #on Sunstone devices
                sunstone_pattern = r'Press RETURN to get started\.$'
                if re.search(sunstone_pattern,output):
                    print("*****Sunstone pattern detected")
                    self.write_channel(TELNET_RETURN)
                    output = self.read_channel(verbose=True)


                # Support direct telnet through terminal server
                if re.search(r"initial configuration dialog\? \[yes/no\]: ", output):
                    self.write_channel("no" + self.TELNET_RETURN)
                    time.sleep(.5 * delay_factor)
                    count = 0
                    while count < 15:
                        output = self.read_channel(verbose=True)
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


                if re.search(rebooted_bmc_prompt_pattern, output) or re.search(bmc_prompt_pattern, output) or re.search(x86_prompt_pattern, output):
                    is_spitfire = True

                # Check if proper data received
                if (pri_prompt_terminator in output or alt_prompt_terminator in output) and is_spitfire == False:
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
        output = self.read_channel(verbose=True)
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
