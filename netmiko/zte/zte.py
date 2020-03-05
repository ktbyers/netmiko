from netmiko.cisco_base_connection import CiscoBaseConnection
import re
import time
from netmiko import log


class ZTEBase(CiscoBaseConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()



    def check_config_mode(self, check_string=")#", pattern="#"):
        """
        Checks if the device is in configuration mode or not.

        """
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(self, cmd="write", confirm=False, confirm_response=""):
        """Saves Config Using Copy Run Start"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

class ZTESSH(ZTEBase):
    pass

class ZTETelnet(ZTEBase):
    
    def disable_paging(self, command="terminal length 0", delay_factor=1):
        """Disable paging default to a Cisco CLI method.

        :param command: Device command to disable pagination of output
        :type command: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        log.debug("In disable_paging")
        log.debug(f"Command: {command}")
        self.write_channel(command)
        # Make sure you read until you detect the command echo (avoid getting out of sync)
        output = self.read_until_prompt_or_pattern(pattern=re.escape(command.strip()))
        log.debug(f"{output}")
        log.debug("Exiting disable_paging")
        return output
    
    
    
