from netmiko.base_connection import BaseConnection
import time


class TeldatSSHuntested(BaseConnection):
    def session_preparation(self):
        # Prompt is *
        self._test_channel_read(pattern=r"\*")
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    # def establish_connection(self, sleep_time=3, verbose=True):
    #    pass

    def disable_paging(self):
        """Teldat doesn't have pagging"""
        pass

    # def find_prompt(self):
    #    pass

    def set_base_prompt(
        self, pri_prompt_terminator="*", alt_prompt_terminator="", delay_factor=1
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

    # def clear_buffer(self):
    #    pass

    # def send_command(self, command_string, delay_factor=1, max_loops=30):
    #    pass

    # def strip_prompt(self, a_string):
    #    pass

    # def strip_command(self, command_string, output):
    #    pass

    def monitor_mode(self, monitor_command="monitor"):
        """Enter monitor mode"""
        if self.check_base_mode():
            return super().config_mode(config_command=monitor_command)
        else:
            raise ValueError("Not in base mode, will not enter monitor mode.")

    def config_mode(self, config_command="configure"):
        """Enter running configuration mode."""
        if self.check_base_mode():
            return super().config_mode(config_command=config_command)
        else:
            raise ValueError("Not in base mode, will not enter configuration mode.")

    def startup_config_mode(self, config_command="p 5"):
        """Enter running configuration mode."""
        if self.check_base_mode():
            return super().config_mode(config_command=config_command)
        else:
            raise ValueError("Not in base mode, will not enter configuration mode.")

    # def exit_mode(self):
    #    pass

    def send_config_set(self, config_commands=None):
        pass

    def save_config(self, cmd="save yes", confirm=False, confirm_response=""):
        """Save Config"""
        # Some devices are slow so match on trailing-prompt if you can
        output = self.send_command(
            command_string=cmd, strip_prompt=False, strip_command=False
        )
        # return super().save_config(
        #     cmd=cmd, confirm=confirm, confirm_response=confirm_response
        # )
        return output

    def cleanup(self, command="logout"):
        """Gracefully exit the SSH session."""
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_base_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'logout'.
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)
        self.write_channel("yes" + self.RETURN)

    # def disconnect(self):
    #    pass

    def enable(self, *args, **kwargs):
        raise AttributeError("Teldat does not have enable mode")

    def check_enable_mode(self, *args, **kwargs):
        raise AttributeError("Teldat does not have enable mode")

    def exit_enable_mode(self, *args, **kwargs):
        raise AttributeError("Teldat does not have enable mode")

    def check_base_mode(self, check_string="*", pattern=None):
        """
        Checks if the device is in base mode or not.
        *
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def check_config_mode(self, check_string="onfig>", pattern=None):
        """
        Checks if the device is in configuration mode or not.
        P4 = Config>
        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def exit_config_mode(self, exit_config=f"{chr(16)}", pattern=r"\*"):
        """
        Exit from configuration mode.
        Send CTRL+P
        TODO: check pattern
        TODO: Test if ask for unsaved changes
        """
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def check_running_config_mode(self, check_string="onfig$", pattern=None):
        """
        Checks if the device is in configuration mode or not.
        P5 = Config$
        """
        return self.check_config_mode(check_string=check_string, pattern=pattern)

    def exit_running_config_mode(self, exit_config=f"{chr(16)}", pattern=r"\*"):
        """
        Exit from configuration mode.
        Send CTRL+P
        TODO: check pattern
        """
        return self.exit_config_mode(exit_config=exit_config, pattern=pattern)

    def telnet_login(
        self,
        pri_prompt_terminator="*",
        alt_prompt_terminator="**",
        username_pattern=r"Username:",
        pwd_pattern=r"Password:",
        delay_factor=1,
        max_loops=60,
    ):
        """Telnet login: can be username/password or just password."""
        super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )
