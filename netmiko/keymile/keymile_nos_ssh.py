import time
import re


from netmiko.cisco.cisco_ios import CiscoIosBase
from netmiko.ssh_exception import (
    NetMikoTimeoutException,
    NetMikoAuthenticationException,
)


class KeymileNOSSSH(CiscoIosBase):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def check_config_mode(self, check_string="", pattern=""):
        """Keymile doesn't use config mode."""
        pass

    def config_mode(self, config_command="", pattern=""):
        """Keymile doesn't use config mode."""
        pass

    def exit_config_mode(self, exit_config="", pattern=""):
        """Keymile doesn't use config mode."""
        pass

    def check_enable_mode(self, check_string="#"):
        return super(KeymileNOSSSH, self).check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable"):
        return super(KeymileNOSSSH, self).enable(cmd=cmd)

    def exit_enable_mode(self, exit_command="exit"):
        return super(KeymileNOSSSH, self).exit_enable_mode(exit_command=exit_command)

    def _test_channel_read(self, count=40, pattern=""):
        """Try to read the channel (generally post login) verify you receive data back.
        Addition: check for substring 'Login incorrect' in output

        :param count: the number of times to check the channel for data
        :type count: int

        :param pattern: Regular expression pattern used to determine end of channel read
        :type pattern: str
        """

        def _increment_delay(main_delay, increment=1.1, maximum=8):
            """Increment sleep time to a maximum value."""
            main_delay = main_delay * increment
            if main_delay >= maximum:
                main_delay = maximum
            return main_delay

        i = 0
        delay_factor = self.select_delay_factor(delay_factor=0)
        main_delay = delay_factor * 0.1
        time.sleep(main_delay * 10)
        new_data = ""
        while i <= count:
            new_data += self._read_channel_timing()
            if new_data:
                for line in new_data.split(self.RETURN):
                    if "Login incorrect" in line:
                        self.paramiko_cleanup()
                        msg = "Authentication failure: unable to connect"
                        msg += "{device_type} {ip}:{port}".format(
                            device_type=self.device_type, ip=self.host, port=self.port
                        )
                        msg += self.RETURN + "Login incorrect"
                        raise NetMikoAuthenticationException(msg)

                if pattern:
                    if re.search(pattern, new_data):
                        break
                else:
                    # no pattern but data
                    break
            else:
                self.write_channel(self.RETURN)
            main_delay = _increment_delay(main_delay)
            time.sleep(main_delay)
            i += 1

        if new_data:
            return ""
        else:
            raise NetMikoTimeoutException("Timed out waiting for data")

    def special_login_handler(self, delay_factor=1):
        """Since Keymile NOS always returns 'True' on paramiko.connect() we
        check the output for substring 'Login incorrect' after connecting"""
        self._test_channel_read(pattern=r">")
