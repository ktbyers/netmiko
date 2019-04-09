from __future__ import print_function
from __future__ import unicode_literals
import time
import re
from netmiko.huawei.huawei_ssh import HuaweiSSH
from netmiko.ssh_exception import NetMikoAuthenticationException
from netmiko import log


class HuaweiTelnet(HuaweiSSH):
    def telnet_login(
        self,
        pri_prompt_terminator=r"]\s*$",
        alt_prompt_terminator=r">\s*$",
        username_pattern=r"(?:user:|username|login|user name)",
        pwd_pattern=r"assword",
        delay_factor=1,
        max_loops=20,
    ):
        """Telnet login for Huawei Devices"""

        delay_factor = self.select_delay_factor(delay_factor)
        password_change_prompt = r"Change now\? \[Y/N\]"
        combined_pattern = r"(" \
                + r"|".join([
                    pri_prompt_terminator,
                    alt_prompt_terminator,
                    password_change_prompt]) \
                + ")"

        output = ""
        return_msg = ""
        i = 1
        while i <= max_loops:
            try:
                # Search for username pattern / send username
                output = self.read_until_pattern(pattern=username_pattern)
                return_msg += output

                self.write_channel(self.username + self.TELNET_RETURN)

                # Search for password pattern, / send password
                output = self.read_until_pattern(pattern=pwd_pattern)
                return_msg += output

                self.write_channel(self.password + self.TELNET_RETURN)

                # Search for router prompt, OR password_change prompt
                output = self.read_until_pattern(pattern=combined_pattern)
                return_msg += output

                if re.search(password_change_prompt, output):
                    self.write_channel("N" + self.TELNET_RETURN)
                    output = self.read_until_pattern(pattern=combined_pattern)
                    return_msg += output

                return return_msg
            except EOFError:
                self.remote_conn.close()
                msg = "Login failed: {}".format(self.host)
                raise NetMikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(0.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return return_msg

        self.remote_conn.close()
        msg = "Login failed: {}".format(self.host)
        raise NetMikoAuthenticationException(msg)
