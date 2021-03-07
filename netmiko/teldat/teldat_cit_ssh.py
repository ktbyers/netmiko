from netmiko.base_connection import BaseConnection
import time


class TeldatSSH(BaseConnection):
    def session_preparation(self):
        # Prompt is *
        self._test_channel_read(pattern=r"\*")
        self.set_base_prompt()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self):
        """Teldat doesn't have pagging"""
        pass

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

    def cleanup(self, command="logout"):
        """Gracefully exit the SSH session."""
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass
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
