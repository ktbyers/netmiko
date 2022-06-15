from __future__ import print_function
from __future__ import unicode_literals
from logger.cafylog import CafyLog
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko.ssh_exception import NetMikoAuthenticationException
import re
import time

log = CafyLog()

class CiscoBsp(CiscoBaseConnection):
    '''
    CiscoBsp is based of CiscoBaseConnection
    '''
    def bmc_to_bsp_prompt(self,bmc_prompt_pattern=r'\s*\#',bsp_prompt_pattern=r']\s*\#',delay_factor=1,max_loops=20):
        '''
        Switch from BMC to BSP prompt

        :param bmc_prompt_pattern: expected BMC prompt
        :param bsp_prompt_pattern: expected BSP prompt
        :param delay_factor: Factor to adjust delays
        :param max_loops: max number of iterations for attempting to switch prompts
        :return:
        '''

        self.TELNET_RETURN = '\n'
        bmc_to_bsp_cmd = "/usr/local/bin/sol.sh"
        delay_factor = self.select_delay_factor(delay_factor)

        i = 1
        output = self.find_prompt()
        while i <= max_loops:
            if re.search(bmc_prompt_pattern, output):
                log.debug("On BMC Prompt")
                log.debug("Sol.sh to enter BSP prompt")
                self.write_channel(bmc_to_bsp_cmd)
                time.sleep(1 * delay_factor)
                self.write_channel(self.TELNET_RETURN)
                time.sleep(1 * delay_factor)
                output = self.find_prompt()

            if re.search(bsp_prompt_pattern, output):
                log.debug("On BSP Prompt")
                return

            i += 1

        if not re.search(bsp_prompt_pattern, output):
            raise ValueError(f"BMC to BSP login failed. Prompt received after {max_loops} max loops is {repr(output)}")

    def bsp_to_bmc_prompt(self,bmc_prompt_pattern=r'\s*\#',bsp_prompt_pattern=r']\s*\#',delay_factor=1, max_loops=20):
        '''
        Switch from BSP to BMC prompt

        :param bmc_prompt_pattern: expected BMC prompt
        :param bsp_prompt_pattern: expected BSP prompt
        :param delay_factor: Factor to adjust delays
        :param max_loops: max number of iterations for attempting to switch prompts
        :return:
        '''

        self.TELNET_RETURN = '\n'
        CTRL_L = "\x0c"
        delay_factor = self.select_delay_factor(delay_factor)

        i = 1
        output = self.find_prompt()
        while i <= max_loops:
            if re.search(bsp_prompt_pattern, output):
                log.debug("On BSP Prompt")
                log.debug("Ctrl + L; press X to enter BMC prompt")
                self.write_channel(CTRL_L)
                time.sleep(1 * delay_factor)
                self.write_channel('x'+self.TELNET_RETURN)
                time.sleep(1 * delay_factor)
                output = self.find_prompt()

            if re.search(bmc_prompt_pattern, output):
                log.debug("On BMC Prompt")
                return

            i += 1

        if not re.search(bmc_prompt_pattern, output):
            raise ValueError(f"BSP to BMC login failed. Prompt received after {max_loops} max loops is {repr(output)}")

    def bmc_login(self,prompt_pattern=r'\s*\#',username_pattern='login',pwd_pattern=r'assword',delay_factor=1, max_loops=20):
        '''
        Handle BMC login prompt

        :param prompt_pattern: expected BMC prompt
        :param username_pattern: username prompt pattern
        :param pwd_pattern: password prompt pattern
        :param delay_factor: Factor to adjust delays
        :param max_loops: max number of iterations for attempting to login to BMC prompt before raising exception
        :return:
        '''

        bmc_username = "root"
        bmc_pass = "0penBmc"
        self.TELNET_RETURN = '\n'

        i = 1
        while i <= max_loops:
            i += 1
            output = self.find_prompt()

            log.debug("Check if we are already on BMC prompt")
            if re.search(prompt_pattern, output):
                log.debug("On BMC Prompt")
                return

            log.debug("Check if BMC Username Prompt detected")
            if re.search(username_pattern, output):
                log.debug(f"BMC Username pattern detected, sending Username={bmc_username}")
                time.sleep(1)
                self.write_channel(bmc_username)
                time.sleep(1 * delay_factor)
                output = self.find_prompt()

            log.debug("Check if BMC Password Prompt detected")
            if re.search(pwd_pattern, output):
                log.debug(f"BMC Password pattern detected, sending Password={bmc_pass}")
                self.write_channel(bmc_pass)
                time.sleep(.5 * delay_factor)
                output = self.find_prompt()

                if re.search(prompt_pattern, output):
                    log.debug("On BMC Prompt")
                    return

                if re.search(pwd_pattern, output):
                    self.write_channel(bmc_pass)
                    time.sleep(.5 * delay_factor)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(.5 * delay_factor)
        output = self.find_prompt()
        if re.search(prompt_pattern, output):
            log.debug("On BMC Prompt")
            return

        raise NetMikoAuthenticationException("LAST_TRY login failed for BMC Prompt")

    def set_base_prompt(self, pri_prompt_terminator='#',alt_prompt_terminator='$', delay_factor=1):
        """Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Cisco
        devices this will be set to router hostname (i.e. prompt without '>' or '#').

        This will be set on entering user exec or privileged exec on Cisco, but not when
        entering/exiting config mode.

        :param pri_prompt_terminator: Primary trailing delimiter for identifying a device prompt
        :type pri_prompt_terminator: str

        :param alt_prompt_terminator: Alternate trailing delimiter for identifying a device prompt
        :type alt_prompt_terminator: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        prompt = self.find_prompt(delay_factor=delay_factor)
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator) and 'bmc' not in prompt:
            raise ValueError(f"BSP prompt not found: {repr(prompt)}")
        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]
        return self.base_prompt

    def disable_paging(self, *args, **kwargs):
        """Paging is disabled by default."""
        return ""

class CiscoBspSSH(CiscoBsp):
    '''
    CiscoBspSSH is based of CiscoBsp -- CiscoBaseConnection
    '''

    pass

class CiscoBspTelnet(CiscoBsp):
    '''
    CiscoBspTelnet is based of CiscoBsp -- CiscoBaseConnection
    '''

    def telnet_login(self,pri_prompt_terminator=r']\s*\#',alt_prompt_terminator=r']\s*\$',username_pattern=r'login',pwd_pattern=r'assword',delay_factor=1,max_loops=20):
        '''
        Telnet login to BSP prompt

        :param pri_prompt_terminator: primary prompt pattern (for root user)
        :param alt_prompt_terminator: alternate prompt pattern (for non-root user eg: cisco user)
        :param username_pattern: username prompt pattern
        :param pwd_pattern: password prompt pattern
        :param delay_factor: Factor to adjust delays
        :param max_loops: max number of iterations for attempting to login to BSP prompt before raising exception
        :return:
        '''

        self.TELNET_RETURN = '\n'
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(1 * delay_factor)
        my_username = self.username
        my_password = self.password
        return_msg = ''
        i = 1
        while i <= max_loops:
            try:
                # self.read_channel which internally calls telnetlib.read_ver_eager() returns empty string
                log.debug("Reading channel for the first time")
                output = self.read_channel()

                # self.find_prompt will return prompt after logging in
                log.debug(f"Output after reading channel for first time: {output}")
                if output == '':
                    time.sleep(2 * delay_factor)
                    log.debug("output is empty, doing find_prompt()")
                    output = self.find_prompt()
                    log.debug(f"Output after doing find_prompt: {output}")
                    return_msg += output

                log.debug("Checking if Password Prompt")
                if re.search(pwd_pattern, output):
                    log.debug("Differentiate whether it is password prompt for BMC or BSP")
                    self.write_channel(self.TELNET_RETURN)
                    output = self.find_prompt()
                    return_msg += output

                log.debug("Checking if BMC prompt")
                if 'bmc' in output:
                    log.debug("BMC Login prompt detected")
                    self.bmc_login()
                    time.sleep(2 * delay_factor)
                    self.bmc_to_bsp_prompt()
                    time.sleep(2 * delay_factor)
                    output = self.find_prompt()
                    return_msg += output

                log.debug("Searching for username pattern")
                if re.search(username_pattern, output):
                    log.debug(f"Username pattern detected, sending Username={my_username}")
                    time.sleep(1)
                    self.write_channel(my_username + self.TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    log.debug(f"After sending username, the output pattern is={output}")

                log.debug("Searching for password pattern")
                if re.search(pwd_pattern, output):
                    self.write_channel(my_password + self.TELNET_RETURN)
                    time.sleep(.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                    if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(alt_prompt_terminator, output,flags=re.M):
                        return return_msg

                    if re.search(pwd_pattern, output):
                        self.write_channel(my_password + self.TELNET_RETURN)
                        time.sleep(.5 * delay_factor)
                        output = self.read_channel()
                        return_msg += output

                # Check for device with no password configured
                if re.search(r"assword required, but none set", output):
                    raise NetMikoAuthenticationException(f"Telnet login failed - Password required, but none set: {self.host}")

                # Check if already on BSP prompt
                if re.findall(pri_prompt_terminator, output) or re.findall(alt_prompt_terminator, output):
                    return return_msg

                self.write_channel(self.TELNET_RETURN)
                time.sleep(.5 * delay_factor)
                i += 1
            except EOFError:
                raise NetMikoAuthenticationException(f"EOFError Telnet login failed: {self.host}")

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if (re.search(pri_prompt_terminator, output, flags=re.M) or re.search(alt_prompt_terminator, output,flags=re.M)):
            return return_msg

        raise NetMikoAuthenticationException(f"LAST_TRY Telnet login failed: {self.host}")
