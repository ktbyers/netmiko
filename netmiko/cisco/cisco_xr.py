import re
from netmiko.cisco_base_connection import CiscoBaseConnection, CiscoFileTransfer


class CiscoXrBase(CiscoBaseConnection):
    def __init__(self, *args, **kwargs):
        # Cisco NX-OS defaults to fast_cli=True and legacy_mode=False
        kwargs.setdefault("fast_cli", True)
        kwargs.setdefault("_legacy_mode", False)
        return super().__init__(*args, **kwargs)

    def establish_connection(self):
        """Establish SSH connection to the network device"""
        super().establish_connection(width=511, height=511)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        # IOS-XR has an issue where it echoes the command even though it hasn't returned the prompt
        self._test_channel_read(pattern=r"[>#]")
        cmd = "terminal width 511"
        self.set_terminal_width(command=cmd, pattern=cmd)
        self.disable_paging()
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def send_config_set(self, config_commands=None, exit_config_mode=False, **kwargs):
        """IOS-XR requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def commit(
        self, confirm=False, confirm_delay=None, comment="", label="", delay_factor=1
    ):
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

        label = str(label)
        error_marker = "Failed to"
        alt_error_marker = "One or more commits have occurred from other"

        # Select proper command string based on arguments provided
        if label:
            if comment:
                command_string = f"commit label {label} comment {comment}"
            elif confirm:
                command_string = "commit label {} confirmed {}".format(
                    label, str(confirm_delay)
                )
            else:
                command_string = f"commit label {label}"
        elif confirm:
            command_string = f"commit confirmed {str(confirm_delay)}"
        elif comment:
            command_string = f"commit comment {comment}"
        else:
            command_string = "commit"

        # Enter config mode (if necessary)
        output = self.config_mode()
        output += self.send_command_expect(
            command_string,
            strip_prompt=False,
            strip_command=False,
            delay_factor=delay_factor,
        )
        if error_marker in output:
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")
        if alt_error_marker in output:
            # Other commits occurred, don't proceed with commit
            output += self.send_command_timing(
                "no", strip_prompt=False, strip_command=False, delay_factor=delay_factor
            )
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")

        return output

    def check_config_mode(self, check_string=")#", pattern=r"[#\$]"):
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

    def exit_config_mode(self, exit_config="end", pattern=""):
        """Exit configuration mode."""
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(exit_config.strip())
                )
            # Read until we detect either an Uncommitted change or the end prompt
            if not re.search(r"(Uncommitted|#$)", output):
                output += self.read_until_pattern(pattern=r"(Uncommitted|#$)")
            if "Uncommitted changes found" in output:
                self.write_channel(self.normalize_cmd("no\n"))
                output += self.read_until_pattern(pattern=r"[>#]")
            if not re.search(pattern, output, flags=re.M):
                output += self.read_until_pattern(pattern=pattern)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def save_config(self, *args, **kwargs):
        """Not Implemented (use commit() method)"""
        raise NotImplementedError


class CiscoXrSSH(CiscoXrBase):
    """Cisco XR SSH driver."""

    pass


class CiscoXrTelnet(CiscoXrBase):
    """Cisco XR Telnet driver."""

    pass


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
            raise ValueError(f"Invalid output from MD5 command: {md5_output}")

    def remote_md5(self, base_cmd="show md5 file", remote_file=None):
        """
        IOS-XR for MD5 requires this extra leading /

        show md5 file /bootflash:/boot/grub/grub.cfg
        """
        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
        # IOS-XR requires both the leading slash and the slash between file-system and file here
        remote_md5_cmd = f"{base_cmd} /{self.file_system}/{remote_file}"
        dest_md5 = self.ssh_ctl_chan.send_command(remote_md5_cmd, max_loops=1500)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
