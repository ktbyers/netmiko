#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 - 2019 Kirk Byers
# Copyright (c) 2014 - 2019 Twin Bridges Technology
# Copyright (c) 2019 NOKIA Inc.
# MIT License - See License file at:
#   https://github.com/ktbyers/netmiko/blob/develop/LICENSE

import re
import time

from netmiko import log
from netmiko.base_connection import BaseConnection


class NokiaSrosSSH(BaseConnection):
    """
    Implement methods for interacting with Nokia SR OS devices.

    Not applicable in Nokia SR OS (disabled):
        - enable()
        - exit_enable_mode()
        - check_enable_mode()

    Overriden methods to adapt Nokia SR OS behavior (changed):
        - session_preparation()
        - set_base_prompt()
        - config_mode()
        - exit_config_mode()
        - check_config_mode()
        - save_config()
        - commit()
        - strip_prompt()
    """

    def session_preparation(self):
        self._test_channel_read()
        self.set_base_prompt()
        # "@" indicates model-driven CLI (vs Classical CLI)
        if "@" in self.base_prompt:
            self.disable_paging(command="environment more false")
            self.set_terminal_width(command="environment console width 512")
        else:
            self.disable_paging(command="environment no more")

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args, **kwargs):
        """Remove the > when navigating into the different config level."""
        cur_base_prompt = super().set_base_prompt(*args, **kwargs)
        match = re.search(r"\*?(.*?)(>.*)*#", cur_base_prompt)
        if match:
            # strip off >... from base_prompt; strip off leading *
            self.base_prompt = match.group(1)
            return self.base_prompt

    def enable(self, *args, **kwargs):
        """Nokia SR OS does not support enable-mode"""
        return ""

    def check_enable_mode(self, *args, **kwargs):
        """Nokia SR OS does not support enable-mode"""
        return True

    def exit_enable_mode(self, *args, **kwargs):
        """Nokia SR OS does not support enable-mode"""
        return ""

    def config_mode(self, *args, **kwargs):
        """Enable config edit-mode for Nokia SR OS"""
        self.write_channel(self.RETURN)
        output = self.read_until_prompt()
        if "@" in self.base_prompt:
            if "(ex)[" not in output:
                self.write_channel(self.normalize_cmd("edit-config exclusive"))
                output += self.read_until_prompt()
            else:
                log.warning("Already in config edit-mode!")
        return output

    def exit_config_mode(self, *args, **kwargs):
        """Disable config edit-mode for Nokia SR OS"""
        self.write_channel(self.normalize_cmd("exit all"))
        output = self.read_until_prompt()
        # Model-driven CLI
        if "@" in self.base_prompt and "(ex)[" in output:
            if "*(ex)[" in output:
                log.warning("Uncommitted changes! Discarding changes!")
                self.write_channel(self.normalize_cmd("discard"))
                output += self.read_until_prompt()
            self.write_channel(self.normalize_cmd("quit-config"))
            output += self.read_until_prompt()
        return output

    def check_config_mode(self, *args, **kwargs):
        """Check config mode for Nokia SR OS"""
        if "@" not in self.base_prompt:
            # Classical CLI
            return True
        else:
            # Model-driven CLI look for "exclusive"
            self.write_channel(self.RETURN)
            output = self.read_until_prompt()
            return "(ex)[" in output

    def save_config(self, *args, **kwargs):
        """Persist configuration to cflash for Nokia SR OS"""
        output = self.send_command(command_string="/admin save")
        return output

    def send_config_set(self, config_commands=None, exit_config_mode=None, **kwargs):
        """Model driven CLI requires you not exit from configuration mode."""
        if exit_config_mode is None:
            # Set to False if model-driven CLI
            exit_config_mode = False if "@" in self.base_prompt else True
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def commit(self, *args, **kwargs):
        """Activate changes from private candidate for Nokia SR OS"""
        self.write_channel(self.normalize_cmd("exit all"))
        output = self.read_until_prompt()
        if "@" in self.base_prompt and "*(ex)[" in output:
            log.info("Apply uncommitted changes!")
            self.write_channel(self.normalize_cmd("commit"))
            output += self.read_until_prompt()
        return output

    def _discard(self):
        """Discard changes from private candidate for Nokia SR OS"""
        self.write_channel(self.normalize_cmd("exit all"))
        output = self.read_until_prompt()
        if "@" in self.base_prompt and "*(ex)[" in output:
            log.info("Discard uncommitted changes!")
            self.write_channel(self.normalize_cmd("discard"))
            output += self.read_until_prompt()
        return output

    def strip_prompt(self, *args, **kwargs):
        """Strip prompt from the output."""
        output = super().strip_prompt(*args, **kwargs)
        if "@" in self.base_prompt:
            # Remove context prompt too
            strips = r"[\r\n]*\!?\*?(\((ex|gl|pr|ro)\))?\[\S*\][\r\n]*"
            return re.sub(strips, "", output)
        else:
            return output
