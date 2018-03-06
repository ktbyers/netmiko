from __future__ import print_function
from __future__ import unicode_literals
import time
import re
from netmiko.cisco_base_connection import CiscoSSHConnection, CiscoFileTransfer


class CiscoXrSSH(CiscoSSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command='terminal width 511')
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def send_config_set(self, config_commands=None, exit_config_mode=True, **kwargs):
        """IOS-XR requires you not exit from configuration mode."""
        return super(CiscoXrSSH, self).send_config_set(config_commands=config_commands,
                                                       exit_config_mode=False, **kwargs)

    def commit(self, confirm=False, confirm_delay=None, comment='', label='', delay_factor=1):
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
        output = self.config_mode()
        output += self.send_command_expect(command_string, strip_prompt=False, strip_command=False,
                                           delay_factor=delay_factor)
        if error_marker in output:
            raise ValueError("Commit failed with the following errors:\n\n{0}".format(output))
        if alt_error_marker in output:
            # Other commits occurred, don't proceed with commit
            output += self.send_command_timing("no", strip_prompt=False, strip_command=False,
                                               delay_factor=delay_factor)
            raise ValueError("Commit failed with the following errors:\n\n{0}".format(output))

        return output

    def check_config_mode(self, check_string=')#', pattern=r"[#\$]"):
        """Checks if the device is in configuration mode or not.

        IOS-XR, unfortunately, does this:
        RP/0/RSP0/CPU0:BNG(admin)#
        """
        self.write_channel(self.RETURN)
        output = self.read_until_pattern(pattern=pattern)
        # Strip out (admin) so we don't get a false positive with (admin)#
        # (admin-config)# would still match.
        output = output.replace("(admin)", "")
        return check_string in output

    def exit_config_mode(self, exit_config='end'):
        """Exit configuration mode."""
        output = ''
        if self.check_config_mode():
            output = self.send_command_timing(exit_config, strip_prompt=False, strip_command=False)
            if "Uncommitted changes found" in output:
                output += self.send_command_timing('no', strip_prompt=False, strip_command=False)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def save_config(self):
        """Not Implemented (use commit() method)"""
        raise NotImplementedError


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
