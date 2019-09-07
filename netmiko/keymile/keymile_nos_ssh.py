import time
import re


from netmiko.cisco.cisco_ios import CiscoIosBase
from netmiko.ssh_exception import NetMikoAuthenticationException


class KeymileNOSSSH(CiscoIosBase):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt()
        self.disable_paging()
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def _test_channel_read(self, count=40, pattern=""):
        """Since Keymile NOS always returns True on paramiko.connect() we
        check the output for substring Login incorrect after connecting."""
        output = super(KeymileNOSSSH, self)._test_channel_read(
            count=count, pattern=pattern
        )
        pattern = r"Login incorrect"
        if re.search(pattern, output):
            self.paramiko_cleanup()
            msg = "Authentication failure: unable to connect"
            msg += "{device_type} {host}:{port}".format(
                device_type=self.device_type, host=self.host, port=self.port
            )
            msg += self.RESPONSE_RETURN + "Login incorrect"
            raise NetMikoAuthenticationException(msg)
        else:
            return output

    def special_login_handler(self, delay_factor=1):
        """Since Keymile NOS always returns True on paramiko.connect() we
        check the output for substring Login incorrect after connecting."""
        self._test_channel_read(pattern=r"(>|Login incorrect)")
