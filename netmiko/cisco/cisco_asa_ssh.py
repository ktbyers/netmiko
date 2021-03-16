"""Subclass specific to Cisco ASA."""
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection, CiscoFileTransfer
from netmiko.ssh_exception import NetmikoAuthenticationException


class CiscoAsaSSH(CiscoSSHConnection):
    """Subclass specific to Cisco ASA."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("fast_cli", True)
        kwargs.setdefault("_legacy_mode", False)
        kwargs.setdefault("allow_auto_change", True)
        return super().__init__(*args, **kwargs)

    def session_preparation(self):
        """Prepare the session after the connection has been established."""

        # Make sure the ASA is ready
        command = "show curpriv\n"
        self.write_channel(command)
        self.read_until_pattern(pattern=re.escape(command.strip()))

        # The 'enable' call requires the base_prompt to be set.
        self.set_base_prompt()
        if self.secret:
            self.enable()
        else:
            self.asa_login()
        self.disable_paging(command="terminal pager 0")

        if self.allow_auto_change:
            try:
                self.send_config_set("terminal width 511")
            except ValueError:
                # Don't fail for the terminal width
                pass
        else:
            # Disable cmd_verify if the terminal width can't be set
            self.global_cmd_verify = False

        self.set_base_prompt()

    def check_config_mode(self, check_string=")#", pattern=r"[>\#]"):
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def enable(
        self,
        cmd="enable",
        pattern="ssword",
        enable_pattern=r"\#",
        re_flags=re.IGNORECASE,
    ):
        return super().enable(
            cmd=cmd, pattern=pattern, enable_pattern=enable_pattern, re_flags=re_flags
        )

    def send_command_timing(self, *args, **kwargs):
        """
        If the ASA is in multi-context mode, then the base_prompt needs to be
        updated after each context change.
        """
        output = super().send_command_timing(*args, **kwargs)
        if len(args) >= 1:
            command_string = args[0]
        else:
            command_string = kwargs["command_string"]
        if "changeto" in command_string:
            self.set_base_prompt()
        return output

    def send_command(self, *args, **kwargs):
        """
        If the ASA is in multi-context mode, then the base_prompt needs to be
        updated after each context change.
        """
        if len(args) >= 1:
            command_string = args[0]
        else:
            command_string = kwargs["command_string"]

        # If changeto in command, look for '#' to determine command is done
        if "changeto" in command_string:
            if len(args) <= 1:
                expect_string = kwargs.get("expect_string", "#")
                kwargs["expect_string"] = expect_string
        output = super().send_command(*args, **kwargs)

        if "changeto" in command_string:
            self.set_base_prompt()

        return output

    def send_command_expect(self, *args, **kwargs):
        """Backwards compaitibility."""
        return self.send_command(*args, **kwargs)

    def set_base_prompt(self, *args, **kwargs):
        """
        Cisco ASA in multi-context mode needs to have the base prompt updated
        (if you switch contexts i.e. 'changeto')

        This switch of ASA contexts can occur in configuration mode. If this
        happens the trailing '(config*' needs stripped off.
        """
        cur_base_prompt = super().set_base_prompt(*args, **kwargs)
        match = re.search(r"(.*)\(conf.*", cur_base_prompt)
        if match:
            # strip off (conf.* from base_prompt
            self.base_prompt = match.group(1)
            return self.base_prompt

    def asa_login(self):
        """
        Handle ASA reaching privilege level 15 using login

        twb-dc-fw1> login
        Username: admin

        Raises NetmikoAuthenticationException, if we do not reach privilege
        level 15 after 10 loops.
        """
        delay_factor = self.select_delay_factor(0)

        i = 1
        max_attempts = 10
        self.write_channel("login" + self.RETURN)
        output = self.read_until_pattern(pattern=r"login")
        while i <= max_attempts:
            time.sleep(0.5 * delay_factor)
            output = self.read_channel()
            if "sername" in output:
                self.write_channel(self.username + self.RETURN)
            elif "ssword" in output:
                self.write_channel(self.password + self.RETURN)
            elif "#" in output:
                return
            else:
                self.write_channel("login" + self.RETURN)
            i += 1

        msg = "Unable to enter enable mode!"
        raise NetmikoAuthenticationException(msg)

    def save_config(self, cmd="write mem", confirm=False, confirm_response=""):
        """Saves Config"""
        return super().save_config(
            cmd=cmd, confirm=confirm, confirm_response=confirm_response
        )

    def normalize_linefeeds(self, a_string):
        """Cisco ASA needed that extra \r\n\r"""
        newline = re.compile("(\r\n\r|\r\r\r\n|\r\r\n|\r\n|\n\r)")
        a_string = newline.sub(self.RESPONSE_RETURN, a_string)
        if self.RESPONSE_RETURN == "\n":
            # Delete any remaining \r
            return re.sub("\r", "", a_string)
        else:
            return a_string


class CiscoAsaFileTransfer(CiscoFileTransfer):
    """Cisco ASA SCP File Transfer driver."""

    pass
