from netmiko.base_connection import BaseConnection
import time

class XirrusSSH(BaseConnection):
    """
    Implement methods for interacting with XIRRUS APs.

    Disables 'enable()' and 'check_enable_mode()' methods.
    """

    def session_preparation(self):
        """
        Prepare the session after the connection has been established.

        Enter config mode.
        Disable paging (the '--more--' prompts).
        Exit config mode.
        """

        self.disable_paging(command="no more")
        self.set_base_prompt()

    def check_enable_mode(self, *args, **kwargs):
        """No enable mode on Xirrus APs."""
        pass

    def enable(self, *args, **kwargs):
        """No enable mode on Xirrus APs."""
        pass

    def exit_enable_mode(self, *args, **kwargs):
        """No enable mode on Xirrus APs."""
        pass
   
    def config_mode(self, config_command='configure'):
        """Enter configuration mode."""
        return super(XirrusSSH, self).config_mode(config_command=config_command)

    def exit_config_mode(self, exit_config='end'):
        """Exit configuration mode."""
        return super(XirrusSSH, self).exit_config_mode(exit_config=exit_config)

    def set_base_prompt(self, pri_prompt_terminator='#',
                        alt_prompt_terminator='>', delay_factor=1):
        """Sets self.base_prompt"""
        #self.read_until_prompt()
        prompt = self.find_prompt(delay_factor=delay_factor)
        print(prompt)
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError("AP Prompt not found: {0}".format(prompt))
        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]
        return self.base_prompt

    def disable_paging(self, command="no more", delay_factor=1):
        """Disable paging default to the xirrus method."""
        debug = True
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * .1)
        self.clear_buffer()
        config = self.normalize_cmd("configure")
        command = self.normalize_cmd(command)
        exit_config = self.normalize_cmd("end")

        if debug:
            print("In disable_paging")
            print("command: {}", format(command))

        self.read_until_prompt()
        self.write_channel(config)
        output = self.read_until_prompt()
        self.write_channel(command)
        output += self.read_until_prompt()
        self.write_channel(exit_config)
        output += self.read_until_prompt()

        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        if debug:
            print(output)
            print("Exiting disable_paging")

        return output
