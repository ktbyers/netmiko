from netmiko.base_connection import BaseConnection
import time
import re
from netmiko import log


class TeldatSSH(BaseConnection):
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
        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple
        contexts. For Teldat this will be the router prompt with * stripped off.

        This will be set on logging in, but not when entering other views
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

    # def monitor_mode(self, monitor_command="p 3"):
    #     """Enter monitor mode"""
    #     # if self.check_base_mode():
    #     #    return super().config_mode(config_command=monitor_command)
    #     # else:
    #     #    raise ValueError("Not in base mode, will not enter monitor mode.")
    #     return super().config_mode(config_command=monitor_command, pattern="+")

    def check_monitor_mode(self, check_string="+", pattern=None):
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def check_config_mode(self, check_string="onfig>", pattern=None):
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def check_running_config_mode(self, check_string="onfig$", pattern=None):
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def monitor_mode(self, monitor_command="p 3", pattern=r"\+", re_flags=0):
        """Enter into monitor_mode.
        On Teldat devices always go to base mode and enter desired mode
        Cannot use super.config_mode() because config mode check is staticly called in BaseConnection

        :param monitor_command: Configuration command to send to the device
        :type monitor_command: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str

        :param re_flags: Regular expression flags
        :type re_flags: RegexFlag
        """
        self.base_mode()

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
            raise ValueError(f"Failed to enter {monitor_command} mode.")
        return output

    def config_mode(self, config_command="p 4", pattern="onfig>", re_flags=0):
        # TODO: consider using monitor_mode instead
        self.base_mode()  # Teldat devices do not allow mode switching, always go to base mode first
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
        exit_config_mode=False,
        delay_factor=1,
        max_loops=150,
        strip_prompt=False,
        strip_command=False,
        config_mode_command=None,
        cmd_verify=True,
        enter_config_mode=False,
    ):
        """
        For Teldat devices until further testing do not enter config mode or exit
        """
        return super().send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            delay_factor=delay_factor,
            max_loops=max_loops,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            config_mode_command=config_mode_command,
            cmd_verify=cmd_verify,
            enter_config_mode=enter_config_mode,
        )

    def exit_config_mode(self):
        return self.base_mode()

    def base_mode(self, exit_cmd="\x10", pattern="\*"):
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