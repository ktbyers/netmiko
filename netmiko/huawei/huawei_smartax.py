import time
import re
from netmiko.cisco_base_connection import CiscoBaseConnection
from netmiko import log
from collections import deque

class HuaweiSmartAXSSH(CiscoBaseConnection):
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def find_prompt(self, delay_factor=1):
        """Finds the current network device prompt, last line only.

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        self.write_channel(self.RETURN)
        sleep_time = delay_factor * 0.1
        time.sleep(sleep_time)

        # Initial attempt to get prompt
        prompt = self.read_channel()
        # Check if the only thing you received was a newline
        count = 0
        prompt = prompt.strip()
        while count <= 12 and not prompt:
            prompt = self.read_channel().strip()
            if not prompt:
                time.sleep(sleep_time)
                if sleep_time <= 3:
                    # Double the sleep_time when it is small
                    sleep_time *= 2
                else:
                    sleep_time += 1
            count += 1

        # If multiple lines in the output take the last line
        prompt = self.normalize_linefeeds(prompt)
        prompt = prompt.split(self.RESPONSE_RETURN)[-1]
        prompt = prompt.strip()
        if not prompt:
            raise ValueError(f"Unable to find prompt: {prompt}")
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        log.debug(f"[find_prompt()]: prompt is {prompt}")
        return prompt

    def send_command_timing(self, command_string="", cmd_verify=False):
        """ Sends Enter if the pattern { <cr> is found in the output.. This is required for SmartAX """
        output = super().send_command_timing(command_string=command_string)

        if r"{ <cr>" in output:
            self.write_channel("\n")

        output += self.read_channel()

        return output

    def send_command_expect(self, *args, **kwargs):
        """  Huawei SmartAX can't disable paging so I've handled output to send \n or space when required  """
        return self.send_command(*args, **kwargs)

    def send_command(
        self,
        command_string,
        expect_string=None,
        delay_factor=1,
        max_loops=500,
        auto_find_prompt=True,
        strip_prompt=True,
        strip_command=True,
        normalize=True,
        cmd_verify=True,
    ):
        """Execute command_string on the SSH channel using a pattern-based mechanism. Generally
        used for show commands. By default this method will keep waiting to receive data until the
        network device prompt is detected. The current network device prompt will be determined
        automatically.

        :param command_string: The command to be executed on the remote device.
        :type command_string: str

        :param expect_string: Regular expression pattern to use for determining end of output.
            If left blank will default to being based on router prompt.
        :type expect_string: str

        :param delay_factor: Multiplying factor used to adjust delays (default: 1).
        :type delay_factor: int

        :param max_loops: Controls wait time in conjunction with delay_factor. Will default to be
            based upon self.timeout.
        :type max_loops: int

        :param strip_prompt: Remove the trailing router prompt from the output (default: True).
        :type strip_prompt: bool

        :param strip_command: Remove the echo of the command from the output (default: True).
        :type strip_command: bool

        :param normalize: Ensure the proper enter is sent at end of command (default: True).
        :type normalize: bool

        Huawei SmartAX can't disable paging so I've handled output to send \n or space when required depending on the output found...

        """
        # Time to delay in each read loop
        loop_delay = 0.2

        # Default to making loop time be roughly equivalent to self.timeout (support old max_loops
        # and delay_factor arguments for backwards compatibility).
        delay_factor = self.select_delay_factor(delay_factor)
        if delay_factor == 1 and max_loops == 500:
            # Default arguments are being used; use self.timeout instead
            max_loops = int(self.timeout / loop_delay)

        # Find the current router prompt
        if expect_string is None:
            if auto_find_prompt:
                try:
                    prompt = self.find_prompt(delay_factor=delay_factor)
                except ValueError:
                    prompt = self.base_prompt
            else:
                prompt = self.base_prompt
            search_pattern = re.escape(prompt.strip())
        else:
            search_pattern = expect_string

        if normalize:
            command_string = self.normalize_cmd(command_string)

        time.sleep(delay_factor * loop_delay)
        self.clear_buffer()
        self.write_channel(command_string)
        new_data = ""

        cmd = command_string.strip()
        # if cmd is just and "enter" skip this section
        if cmd:
            log.debug(f"cmd is: {cmd}")
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            new_data = self.read_until_pattern(pattern=re.escape(cmd))
            new_data = self.normalize_linefeeds(new_data)
            # Strip off everything before the command echo (to avoid false positives on the prompt)
            if new_data.count(cmd) == 1:
                new_data = new_data.split(cmd)[1:]
                new_data = self.RESPONSE_RETURN.join(new_data)
                new_data = new_data.lstrip()
                new_data = f"{cmd}{self.RESPONSE_RETURN}{new_data}"

        i = 1
        output = ""
        past_three_reads = deque(maxlen=3)
        first_line_processed = False

        # Keep reading data until search_pattern is found or until max_loops is reached.
        while i <= max_loops:
            if new_data:
                output += new_data
                past_three_reads.append(new_data)

                # Case where we haven't processed the first_line yet (there is a potential issue
                # in the first line (in cases where the line is repainted).
                if not first_line_processed:
                    output, first_line_processed = self._first_line_handler(
                        output, search_pattern
                    )
                    # Check if we have already found our pattern
                    if re.search(search_pattern, output):
                        break

                else:
                    # Check if pattern is in the past three reads
                    if re.search(search_pattern, "".join(past_three_reads)):
                        break

            if r"{ <cr" in new_data:
                log.debug("Found pattern { <cr in read_channel")
                # Send Enter to continue in Huawei SmartAX Prompt
                self.write_channel("\n")

            if r"---- More" in new_data:
                log.debug("Found pattern '---- More' in read_channel")
                # Send Space to continue getting output... This is required on SmartAX devices because they can't fully disable the Paging
                self.write_channel(" ")

            time.sleep(delay_factor * loop_delay)
            i += 1
            new_data = self.read_channel()
        else:  # nobreak
            raise IOError(
                "Search pattern never detected in send_command_expect: {}".format(
                    search_pattern
                )
            )

        output = self._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )

        return output

    def disable_paging(self, command="scroll", delay_factor=1):

        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        log.debug("in disable_paging")
        log.debug(f"Command: {command}")
        self.send_command(command) #Can't use write_channel because { <cr> } output we need to handle on SmartAX Devices
    log.debug("Exiting disable_paging")

    def config_mode(self, config_command="config", pattern=""):
        """Enter configuration mode."""
        if not pattern:
            pattern = re.escape(self.base_prompt[:16])
        return super().config_mode(config_command=config_command, pattern=pattern)

    def check_config_mode(self, check_string=")#", pattern="#"):
        return super().check_config_mode(check_string=check_string, pattern=pattern)  # pattern

    def exit_config_mode(self, exit_config="quit"):
        return super().exit_config_mode(exit_config=exit_config)

    def check_enable_mode(self, check_string="#"):
        return super().check_enable_mode(check_string=check_string)

    def enable(self, cmd="enable", pattern="", re_flags=re.IGNORECASE):
        return super().enable(cmd=cmd, pattern=pattern, re_flags=re_flags)  # pattern

    def exit_enable_mode(self, exit_command="disable"):
        return super().exit_enable_mode(exit_command=exit_command)

    def set_base_prompt(self, pri_prompt_terminator=">", alt_prompt_terminator="#"):
        return super().set_base_prompt(pri_prompt_terminator=pri_prompt_terminator, alt_prompt_terminator=alt_prompt_terminator)

    def save_config(self, cmd="save", confirm=False, confirm_response=""):
        """ Save Config for HuaweiSSH"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )
