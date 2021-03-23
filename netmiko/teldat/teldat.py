from netmiko.base_connection import BaseConnection
import time
import re
from netmiko import log


class TeldatBase(BaseConnection):
    def session_preparation(self):
        # Prompt is "*"
        self._test_channel_read(pattern=r"\*")
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self):
        """Teldat doesn't have pagging"""
        pass

    def set_base_prompt(
        self, pri_prompt_terminator="*", alt_prompt_terminator="*", delay_factor=1
    ):
        """
        Teldat base prompt is "hostname *"
        """
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
        )

    def cleanup(self, command="logout"):
        """Gracefully exit the SSH session."""
        self.base_mode()
        # Always try to send final 'logout'.
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)
        self.write_channel("yes" + self.RETURN)

    def enable(self, *args, **kwargs):
        raise AttributeError("Teldat does not have enable mode")

    def check_enable_mode(self, *args, **kwargs):
        raise AttributeError("Teldat does not have enable mode")

    def exit_enable_mode(self, *args, **kwargs):
        raise AttributeError("Teldat does not have enable mode")

    def check_monitor_mode(self, check_string="+", pattern=None):
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def check_config_mode(self, check_string="onfig>", pattern=None):
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def check_running_config_mode(self, check_string="onfig$", pattern=None):
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def monitor_mode(self, monitor_command="p 3", pattern=r"\+", re_flags=0):
        """
        Enter into monitor_mode.
        On Teldat devices always go to base mode before entering other modes
        Cannot reuse super.config_mode() because config mode check is called only with defaults in BaseConnection
        """
        self.base_mode()  # Teldat devices do not allow inter mode switching, always go to base mode first

        output = ""
        self.write_channel(self.normalize_cmd(monitor_command))
        # Make sure you read until you detect the command echo (avoid getting out of sync)
        if self.global_cmd_verify is not False:
            output += self.read_until_pattern(
                pattern=re.escape(monitor_command.strip())
            )
        if not re.search(pattern, output, flags=re_flags):
            output += self.read_until_pattern(pattern=pattern, re_flags=re_flags)
        if not self.check_monitor_mode():
            raise ValueError(f"Failed to enter monitor mode.")
        return output

    def config_mode(self, config_command="p 4", pattern="onfig>", re_flags=0):
        # TODO: consider reusing monitor_mode
        self.base_mode()
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def running_config_mode(self, config_command="p 5", pattern=r"onfig\$", re_flags=0):
        """
        Enter running config mode
        """
        self.base_mode()

        output = ""
        self.write_channel(self.normalize_cmd(config_command))
        # Make sure you read until you detect the command echo (avoid getting out of sync)
        if self.global_cmd_verify is not False:
            output += self.read_until_pattern(pattern=re.escape(config_command.strip()))
        if not re.search(pattern, output, flags=re_flags):
            output += self.read_until_pattern(pattern=pattern, re_flags=re_flags)
        if not self.check_running_config_mode():
            raise ValueError(f"Failed to enter running config mode.")
        return output

    def send_config_set(
        self,
        config_commands=None,
        enter_config_mode=False,
        config_mode_command=None,
        exit_config_mode=False,
        **kwargs,
    ):
        """
        For Teldat devices until further testing do not enter config mode or exit
        """
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            config_mode_command=config_mode_command,
            enter_config_mode=enter_config_mode,
            **kwargs,
        )

    def save_config(self, cmd="save yes", confirm=False, confirm_response=""):
        if not self.check_config_mode() or not self.check_running_config_mode():
            raise ValueError("Cannot save if not in config or running config mode")
        # Some devices are slow so match on trailing-prompt if you can
        output = self.send_command(
            command_string=cmd, strip_prompt=False, strip_command=False
        )
        return output

    def exit_config_mode(self):
        return self.base_mode()

    def base_mode(self, exit_cmd="\x10", pattern=r"\*"):
        """
        Exit from other modes (monitor, config, running config).
        Send CTRL+P to the device
        """
        output = ""
        self.write_channel(self.normalize_cmd(exit_cmd))
        # Teldat - exit_cmd not printable
        output += self.read_until_pattern(pattern=pattern)
        log.debug(f"base_mode: {output}")
        return output


class TeldatSSH(TeldatBase):
    pass


class TeldatTelnet(TeldatBase):
    def telnet_login(
        self,
        pri_prompt_terminator=r"\*",
        alt_prompt_terminator=r"\*",
        username_pattern=r"Username:",
        pwd_pattern=r"Password:",
        delay_factor=1,
        max_loops=60,
    ):
        super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )