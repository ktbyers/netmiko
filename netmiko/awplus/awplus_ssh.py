from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer
import re
import time


class AwplusBase(BaseConnection):
    """
    Implement methods for interacting with Allied Telesis devices.

    """

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        """ AWPlus Configuration """
        self.disable_paging(command="term len 0")
        time.sleep(0.3 * self.global_delay_factor)


    def _enter_shell(self):
        """Enter the Bourne Shell."""
        return self.send_command("start shell sh", expect_string=r"[\$#]")

    def _return_cli(self):
        """Return to the Awplus CLI."""
        return self.send_command("exit", expect_string=r"[#>]")

    def check_enable_mode(self, check_string="#"):
        """Check if in enable mode. Return boolean."""
        return super().check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable", pattern="ssword", re_flags=re.IGNORECASE):
        """Enter enable mode."""
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)

    def exit_enable_mode(self, exit_command="disable"):
        """Exits enable (privileged exec) mode."""
        return super().exit_enable_mode(exit_command=exit_command)

    def config_mode(self, config_command="configure terminal"):
        """Enter configuration mode."""
        return super().config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config="exit"):
        """Exit configuration mode."""
        output = ""
        if self.check_config_mode():
            output = self.send_command_timing(
                exit_config, strip_prompt=False, strip_command=False
            )
            if "Exit with uncommitted changes?" in output:
                output += self.send_command_timing(
                    "yes", strip_prompt=False, strip_command=False
                )
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        return output

    def cleanup(self, command="exit"):
        """Gracefully exit the SSH session."""
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'exit' (command)
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)


class AwplusSSH(AwplusBase):
    pass


class AwplusTelnet(AwplusBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get("default_enter")
        kwargs["default_enter"] = "\r\n" if default_enter is None else default_enter
        super().__init__(*args, **kwargs)


class AwplusFileTransfer(BaseFileTransfer):
    """Awplus SCP File Transfer driver."""

    def __init__(
        self,
        ssh_conn,
        source_file,
        dest_file,
        file_system="/var/tmp",
        direction="put",
        **kwargs,
    ):
        return super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            **kwargs,
        )

    def remote_space_available(self, search_pattern=""):
        """Return space available on remote device."""
        return self._remote_space_available_unix(search_pattern=search_pattern)

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        return self._check_file_exists_unix(remote_cmd=remote_cmd)

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        return self._remote_file_size_unix(
            remote_cmd=remote_cmd, remote_file=remote_file
        )

    def remote_md5(self, base_cmd="file checksum md5", remote_file=None):
        return super().remote_md5(base_cmd=base_cmd, remote_file=remote_file)

    def enable_scp(self, cmd=None):
        raise NotImplementedError

    def disable_scp(self, cmd=None):
        raise NotImplementedError
