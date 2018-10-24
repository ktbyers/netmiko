from __future__ import unicode_literals


from netmiko.base_connection import BaseConnection
import re

class EndaceSSH(BaseConnection):

    
    def establish_connection(self, width=None, height=None):
        return super(EndaceSSH, self).establish_connection(
            width=width, height=height
        )

    def disable_paging(self, command="no cli session paging enable", delay_factor=1):
        return super(EndaceSSH, self).disable_paging(
            command=str(command), delay_factor=delay_factor
        )

    def session_preparation(self):
        #self.ansi_escape_codes = True
        return super(EndaceSSH, self).session_preparation()

    def check_enable_mode(self, check_string="#"):
        #Check if in enable mode. Return boolean.
        return super(EndaceSSH, self).check_enable_mode(
            check_string=str(check_string)
        )

    def enable(self, cmd='enable', pattern='', re_flags=re.IGNORECASE):
        return super(EndaceSSH, self).enable(
            cmd=str(cmd), pattern=str(pattern), re_flags=re_flags
        )

    def exit_enable_mode(self, exit_command='disable'):
        return super(EndaceSSH, self).exit_enable_mode(
            exit_command=str(exit_command)
        )

    def check_config_mode(self, check_string='(config) #'):
        return super(EndaceSSH, self).check_config_mode(
            check_string=str(check_string)
        )

    def config_mode(self, config_command='conf t', pattern=''):
        output = ""
        if self.check_enable_mode():
            if self.check_config_mode():
                return output
            else:
                output = self.send_command_timing(
                    str(config_command), strip_command=False, strip_prompt=False
                )
                if "to enter configuration mode anyway" in output:
                    output += self.send_command_timing(
                        str("YES"), strip_command=False, strip_prompt=False
                    )
                if self.check_config_mode():
                    return output
                else:
                    raise ValueError("Failed to enter configuration mode")
        else:
            self.enable()
            self.config_mode()

    def exit_config_mode(self, exit_config='exit', pattern='#'):
        return super(EndaceSSH, self).exit_config_mode(
            exit_config = str(exit_config), pattern=str(pattern)
        )

    def cleanup(self):
        if self.check_config_mode():
            self.exit_config_mode()
        self._session_log_fin=True
        self.write_channel("exit" + self.RETURN)

    def save_config(self, cmd=str('configuration write'), confirm=True, confirm_response=''):
        while True:
            if self.check_enable_mode():
                if self.check_config_mode():
                    self.send_command_timing(
                        cmd, strip_command=False, strip_prompt=False
                    )
                    return
                self.config_mode()
                self.send_command_timing(
                    cmd, strip_command=False, strip_prompt=False
                )
                return
            self.enable()
            self.config_mode()
            self.send_command_timing(
                cmd, strip_command=False, strip_prompt=False
            )

    def find_prompt(self, delay_factor=1):
        return super(EndaceSSH, self).find_prompt(
            delay_factor=delay_factor
        )

    def clear_buffer(self):
        return super(EndaceSSH, self).clear_buffer()

    def send_command(self, command_string, expect_string=None,
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True, normalize=True,
                     use_textfsm=False):
        return super(EndaceSSH, self).send_command(
            command_string=str(command_string),
            expect_string=expect_string,
            delay_factor=delay_factor,
            max_loops=max_loops,
            auto_find_prompt=auto_find_prompt,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            normalize=normalize,
            use_textfsm=use_textfsm
        )

    def strip_prompt(self, a_string):
        return super(EndaceSSH, self).strip_prompt(
            a_string=str(a_string)
        )

    def strip_command(self, command_string, output):
        return super(EndaceSSH, self).strip_command(
            command_string=str(command_string),
            output=str(output)
        )

    def normalize_linefeeds(self, a_string):
        return super(EndaceSSH, self).normalize_linefeeds(
            a_string=str(a_string)
        )

    def send_config_set(self, config_commands=None, exit_config_mode=True, delay_factor=1,
                        max_loops=150, strip_prompt=False, strip_command=False,
                        config_mode_command=None):
        return super(EndaceSSH, self).send_config_set(
            config_commands=config_commands,
            exit_config_mode=exit_config_mode,
            delay_factor=delay_factor,
            max_loops=max_loops,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            config_mode_command=str(config_mode_command)
        )

    def disconnect(self):
        return super(EndaceSSH, self).disconnect()
