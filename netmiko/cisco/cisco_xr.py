from typing import Optional, Any, Union, Sequence, Iterator, TextIO
import re
import warnings
from netmiko.base_connection import DELAY_FACTOR_DEPR_SIMPLE_MSG
from netmiko.cisco_base_connection import CiscoBaseConnection, CiscoFileTransfer


class CiscoXrBase(CiscoBaseConnection):
    def establish_connection(self, width: int = 511, height: int = 511) -> None:
        """Establish SSH connection to the network device"""
        super().establish_connection(width=width, height=height)

    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established."""
        # IOS-XR has an issue where it echoes the command even though it hasn't returned the prompt
        self._test_channel_read(pattern=r"[>#]")
        cmd = "terminal width 511"
        self.set_terminal_width(command=cmd, pattern=cmd)
        self.disable_paging()
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Cisco IOS-XR abbreviates the prompt at 31-chars in config mode.

        Consequently, abbreviate the base_prompt
        """
        base_prompt = super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )
        self.base_prompt = base_prompt[:31]
        return self.base_prompt

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """IOS-XR requires you not exit from configuration mode."""
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def commit(
        self,
        confirm: bool = False,
        confirm_delay: Optional[int] = None,
        comment: str = "",
        label: str = "",
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
    ) -> str:
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

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

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
        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)
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

        # IOS-XR might do this:
        # This could be a few minutes if your config is large. Confirm? [y/n][confirm]
        new_data = self._send_command_str(
            command_string,
            expect_string=r"(#|onfirm)",
            strip_prompt=False,
            strip_command=False,
            read_timeout=read_timeout,
        )
        if "onfirm" in new_data:
            output += new_data
            new_data = self._send_command_str(
                "y",
                expect_string=r"#",
                strip_prompt=False,
                strip_command=False,
                read_timeout=read_timeout,
                cmd_verify=False,
            )
        output += new_data
        if error_marker in output:
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")
        if alt_error_marker in output:
            # Other commits occurred, don't proceed with commit
            output += self._send_command_timing_str(
                "no", strip_prompt=False, strip_command=False, cmd_verify=False
            )
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")

        return output

    def check_config_mode(
        self,
        check_string: str = ")#",
        pattern: str = r"[#\$]",
        force_regex: bool = False,
    ) -> bool:
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

    def exit_config_mode(self, exit_config: str = "end", pattern: str = "") -> str:
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
            if "Uncommitted" in output:
                self.write_channel(self.normalize_cmd("no\n"))
                output += self.read_until_pattern(pattern=r"[>#]")
            if not re.search(pattern, output, flags=re.M):
                output += self.read_until_pattern(pattern=pattern)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def save_config(self, *args: Any, **kwargs: Any) -> str:
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

    @staticmethod
    def process_md5(md5_output: str, pattern: str = r"^([a-fA-F0-9]+)$") -> str:
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

    def remote_md5(
        self, base_cmd: str = "show md5 file", remote_file: Optional[str] = None
    ) -> str:
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
        dest_md5 = self.ssh_ctl_chan._send_command_str(remote_md5_cmd, read_timeout=300)
        dest_md5 = self.process_md5(dest_md5)
        return dest_md5

    def enable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError

    def disable_scp(self, cmd: str = "") -> None:
        raise NotImplementedError
