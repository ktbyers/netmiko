from __future__ import print_function
from __future__ import unicode_literals

import re
import time
#from logger.cafylog import CafyLog
#log = CafyLog()
import logging


# This will create a file named 'test.log' in your current directory.
# It will log all reads and writes on the SSH channel.
#logging.basicConfig(filename='test_netmiko.log', level=logging.DEBUG)
#logger = logging.getLogger("netmiko")

from netmiko.cisco_base_connection import CiscoBaseConnection


class CiscoXr(CiscoBaseConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established.
        When router in 'run' (linux $) prompt, switch back to XR prompt
        """

        username_pattern=r"(sername)|(ogin)"
        pwd_pattern=r"assword"
        self.set_base_prompt(alt_prompt_terminator='$')
        switch_to_xr_command = 'xr'
        if self.find_prompt().endswith('$'):
            if self._check_for_thinxr_host_prompt() == False:
                self.send_command(switch_to_xr_command, expect_string='#')
                self.base_prompt = self.find_prompt()
        #The below block is added to address getting username/login prompt When
        #the box is reloaded
        elif username_pattern in self.find_prompt():
            elf.send_command(self.username, expect_string=pwd_pattern)
            #time.sleep(1 * delay_factor)
            self.send_command(self.password, expect_string='#')
            #time.sleep(.5 * delay_factor)
            self.base_prompt = self.find_prompt()
            if pri_prompt_terminator in self.base_prompt:
                raise ValueError("Could not go to $prompt")

        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')

    def _check_for_thinxr_host_prompt(self, pri_prompt_terminator='#',
                     username_pattern=r"(sername)|(ogin)", pwd_pattern=r"assword",
                     delay_factor=1, max_loops=60):
        SSH_RETURN = '\r\n'
        linux_prompt_pattern = "[xr:~]$"
        switch_to_xr_command = 'xr'
        output = ''
        return_msg = ''
        if self.find_prompt() == linux_prompt_pattern:
            self.write_channel(SSH_RETURN + "xr" + SSH_RETURN)
            delay_factor = self.select_delay_factor(delay_factor)
            time.sleep(1 * delay_factor)
            output = self.read_channel()
            return_msg += output

            # Search for username pattern / send username and then expect Password
            #pattern and send password and expect xr prompt'#'
            if re.search(username_pattern, output):
                self.send_command(self.username, expect_string=pwd_pattern)
                #time.sleep(1 * delay_factor)
                self.send_command(self.password, expect_string='#')
                #time.sleep(.5 * delay_factor)
                self.base_prompt = self.find_prompt()
                if pri_prompt_terminator in self.base_prompt:
                    return True
        else:
            return False


    def config_mode(self, config_command='config term', pattern='', skip_check=True):
        """
        Enter into configuration mode on remote device.

        Cisco IOSXR devices abbreviate the prompt at 20 chars in config mode
        """
        if not pattern:
            #pattern = self.base_prompt[:16]
            #pattern = self.current_prompt[:16]
            pattern = self.base_prompt[:16]
            pattern = self.current_prompt[:16]
        pattern = pattern + ".*config"
        return super(CiscoBaseConnection, self).config_mode(config_command=config_command,
                                                            pattern=pattern,
                                                            skip_check=skip_check)

    def send_config_set(self, config_commands=None, exit_config_mode=True, **kwargs):
        """IOS-XR requires you not exit from configuration mode."""
        return super(CiscoXr, self).send_config_set(config_commands=config_commands,
                                                       exit_config_mode=False, **kwargs)

    def commit(self, confirm=False, confirm_delay=None, comment='', label='',
               replace=False,
               delay_factor=1,
               max_timeout=30, **kwargs):
        """
        Commit the candidate configuration.

        default (no options):
            command_string = commit
        confirm and confirm_delay:
            command_string = commit confirmed <confirm_delay>
        label (which is a label name):
            command_string = commit label <label>
        comment:
            command_string = commit comment <comment>

        supported combinations
        label and confirm:
            command_string = commit label <label> confirmed <confirm_delay>
        label and comment:
            command_string = commit label <label> comment <comment>

        All other combinations will result in an exception.

        failed commit message:
        % Failed to commit one or more configuration items during a pseudo-atomic operation. All
        changes made have been reverted. Please issue 'show configuration failed [inheritance]'
        from this session to view the errors

        message XR shows if other commits occurred:
        One or more commits have occurred from other configuration sessions since this session
        started or since the last commit was made from this session. You can use the 'show
        configuration commit changes' command to browse the changes.

        Exit of configuration mode with pending changes will cause the changes to be discarded and
        an exception to be generated.
        """
        delay_factor = self.select_delay_factor(delay_factor)
        if confirm and not confirm_delay:
            raise ValueError("Invalid arguments supplied to XR commit")
        if confirm_delay and not confirm:
            raise ValueError("Invalid arguments supplied to XR commit")
        if comment and confirm:
            raise ValueError("Invalid arguments supplied to XR commit")

        # wrap the comment in quotes
        # wrap the comment in quotes
        if comment:
            if '"' in comment:
                raise ValueError("Invalid comment contains double quote")
            comment = '"{0}"'.format(comment)

        label = str(label)
        error_marker = 'Failed to'
        alt_error_marker = 'One or more commits have occurred from other'

        # Select proper command string based on arguments provided
        if label:
            if comment:
                command_string = 'commit label {0} comment {1}'.format(label, comment)
            elif confirm:
                command_string = 'commit label {0} confirmed {1}'.format(label, str(confirm_delay))
            else:
                command_string = 'commit label {0}'.format(label)
        elif confirm:
            command_string = 'commit confirmed {0}'.format(str(confirm_delay))
        elif comment:
            command_string = 'commit comment {0}'.format(comment)
        else:
            command_string = 'commit'

        # Enter config mode (if necessary)
        #output = self.config_mode()
        output = ''
        if replace:
            output += self.send_command_timing('commit replace', strip_prompt=False, strip_command=False,
                                               delay_factor=delay_factor,
                                               max_timeout=max_timeout)
            commit_replace_marker = "This commit will replace or remove the entire running configuration"
            if commit_replace_marker in output:
                output += self.send_command_timing("yes", strip_prompt=False, strip_command=False,
                                                   delay_factor=delay_factor,
                                                   max_timeout=max_timeout)
                return output
                                   
        else: 
            try:                 
                output += self.send_command_expect(command_string, strip_prompt=False, strip_command=False,
                                                   delay_factor=delay_factor, **kwargs)
                if error_marker in output:
                    raise ValueError("Commit failed with the following errors:\n\n{0}".format(output))
                else:
                    return output
            except Exception as err:
                output = str(err)
                if alt_error_marker in output:
                    # Other commits occurred, don't proceed with commit
                    output += self.send_command_timing("no", strip_prompt=False, strip_command=False,
                                                           delay_factor=delay_factor)
                    raise ValueError("Commit failed with the following errors:\n\n{0}".format(output))
                else:
                    raise err


    def check_config_mode(self, check_string=')#', pattern=r"[#\$]"):
        """Checks if the device is in configuration mode or not.

        IOS-cXR, unfortunately, does this:
        RP/0/RSP0/CPU0:BNG(admin)#
        """
        self.write_channel('\n')
        output = self.read_until_pattern(pattern=pattern)
        # Strip out (admin) so we don't get a false positive with (admin)#
        # (admin-config)# would still match.
        output = output.replace("(admin)", "")
        return check_string in output

    
    def exit_config_mode(self, exit_config='end', skip_check=False):
        """Exit configuration mode."""
        output = ''
        
        if skip_check or self.check_config_mode():
            output = self.send_command_timing(exit_config, strip_prompt=False,
                        strip_command=False)
            if "Uncommitted changes found" in output:
                output += self.send_command_timing('no\n', strip_prompt=False, strip_command=False)

            if skip_check:
                return output
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    @staticmethod
    def normalize_linefeeds(a_string):
        """Convert '\r\n','\r\r\n', '\n\r', or '\r' to '\n."""
        newline = re.compile(r'(\r\r\n|\r\n|\n\r|\r)')
        return newline.sub('\n', a_string)

class CiscoXrSSH(CiscoXr):
    '''
    CiscoXrSSH is based of CiscoXr -- CiscoBaseConnection
    '''
    pass

class CiscoXrTelnet(CiscoXr):
    '''
    CiscoXrTelnet is based of CiscoXr -- CiscoBaseConnection
    '''
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()

        if 'RP Node is not ' in self.find_prompt():
            # Incase of standby - skip rest of section
            return
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')

    def set_base_prompt(self, pri_prompt_terminator='#',
                        alt_prompt_terminator='>', delay_factor=1,
                        standby_prompt='RP Node is not ',
                       ):
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Cisco
        devices this will be set to router hostname (i.e. prompt without '>' or '#').

        This will be set on entering user exec or privileged exec on Cisco, but not when
        entering/exiting config mode.
        """
        prompt = self.find_prompt(delay_factor=delay_factor)
        list_of_valid_prompts = []
        list_of_valid_prompts.append(pri_prompt_terminator)
        list_of_valid_prompts.append(alt_prompt_terminator)
        if standby_prompt in prompt:
            self.base_prompt = prompt
            return self.base_prompt
        if not prompt[-1] in list_of_valid_prompts:
            raise ValueError("Router prompt not found: {0}".format(prompt))
        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]
        return self.base_prompt

class CiscoCxrHa(CiscoXrTelnet):
    def find_prompt(self, delay_factor=1, pattern=r'[a-z0-9]$', verbose=False, telnet_return='\n'):
        return super().find_prompt(delay_factor=delay_factor, pattern=pattern, verbose=verbose, telnet_return='\r\n')
        
class CiscoXrFileTransfer(CiscoFileTransfer):
    """Cisco IOS-XR SCP File Transfer driver."""
    def process_md5(self, md5_output, pattern=r"^([a-fA-F0-9]+)$"):
        """
        IOS-XR defaults with timestamps enabled
        # show md5 file /bootflash:/boot/grub/grub.cfg
        Sat Mar  3 17:49:03.596 UTC
        c84843f0030efd44b01343fdb8c2e801
        """
        match = re.search(pattern, md5_output, flags=re.M)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid output from MD5 command: {}".format(md5_output))

    def remote_md5(self, base_cmd='show md5 file', remote_file=None):
        """
        IOS-XR for MD5 requires this extra leading /
        show md5 file /bootflash:/boot/grub/grub.cfg
        """
        if remote_file is None:
            if self.direction == 'put':
                remote_file = self.dest_file
            elif self.direction == 'get':
                remote_file = self.source_file
        # IOS-XR requires both the leading slash and the slash between file-system and file here
        remote_md5_cmd = "{} /{}/{}".format(base_cmd, self.file_system, remote_file)
        dest_md5 = self.ssh_ctl_chan.send_command(remote_md5_cmd, max_loops=1500)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
>>>>>>> Telnet fixes for moving to netmiko2
