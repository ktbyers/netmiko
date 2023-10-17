#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 - 2022 Kirk Byers
# Copyright (c) 2014 - 2022 Twin Bridges Technology
# Copyright (c) 2019 - 2020 NOKIA Inc.
# MIT License - See License file at:
#   https://github.com/ktbyers/netmiko/blob/develop/LICENSE

import re
import os
import time
from typing import Any, Optional, Union, Sequence, Iterator, TextIO, Callable

from netmiko import log
from netmiko.base_connection import BaseConnection
from netmiko.scp_handler import BaseFileTransfer
from netmiko.utilities import nokia_context_filter


class NokiaSros(BaseConnection):
    """
    Implement methods for interacting with Nokia SR OS devices
    for both SSH and telnet.

    Not applicable in Nokia SR OS (disabled):
        - exit_enable_mode()

    Overriden methods to adapt Nokia SR OS behavior (changed):
        - session_preparation()
        - set_base_prompt()
        - config_mode()
        - exit_config_mode()
        - check_config_mode()
        - save_config()
        - commit()
        - strip_prompt()
        - enable()
        - check_enable_mode()
    """

    def session_preparation(self) -> None:
        self._test_channel_read()
        self.set_base_prompt()
        # "@" indicates model-driven CLI (vs Classical CLI)
        if "@" in self.base_prompt:
            self._disable_complete_on_space()
            self.set_terminal_width(
                command="environment console width 512", pattern="environment"
            )
            self.disable_paging(command="environment more false")
            self.disable_paging(command="//environment no more")
        else:
            # Classical CLI has no method to set the terminal width nor to disable command
            # complete on space; consequently, cmd_verify needs disabled.
            # Only disabled if not set under the ConnectHandler.
            if self.global_cmd_verify is None:
                self.global_cmd_verify = False
            # Disable paging in both modes, file operations require no paging in classic
            self.disable_paging(command="//environment more false")
            self.disable_paging(command="environment no more", pattern="environment")

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def set_base_prompt(self, *args: Any, **kwargs: Any) -> str:
        """Remove the > when navigating into the different config level."""
        cur_base_prompt = super().set_base_prompt(*args, **kwargs)
        match = re.search(r"\*?(.*?)(>.*)*#", cur_base_prompt)
        if match:
            # strip off >... from base_prompt; strip off leading *
            self.base_prompt: str = match.group(1)

        return self.base_prompt

    def _disable_complete_on_space(self) -> str:
        """
        SR-OS tries to auto complete commands when you type a "space" character.

        This is a bad idea for automation as what your program is sending no longer matches
        the command echo from the device, so we disable this behavior.
        """
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(delay_factor * 0.1)
        command = "environment command-completion space false"
        self.write_channel(self.normalize_cmd(command))
        time.sleep(delay_factor * 0.1)
        return self.read_channel()

    def enable(
        self,
        cmd: str = "enable",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enable SR OS administrative mode"""
        if "@" not in self.base_prompt:
            cmd = "enable-admin"
        return super().enable(
            cmd=cmd,
            pattern=pattern,
            enable_pattern=enable_pattern,
            check_state=check_state,
            re_flags=re_flags,
        )

    def check_enable_mode(self, check_string: str = "in admin mode") -> bool:
        """Check if in enable mode."""
        cmd = "enable"
        if "@" not in self.base_prompt:
            cmd = "enable-admin"
        self.write_channel(self.normalize_cmd(cmd))
        output = self.read_until_prompt_or_pattern(
            pattern="ssword", read_entire_line=True
        )
        if "ssword" in output:
            self.write_channel(self.RETURN)  # send ENTER to pass the password prompt
            self.read_until_prompt(read_entire_line=True)
        return check_string in output

    def exit_enable_mode(self, *args: Any, **kwargs: Any) -> str:
        """Nokia SR OS does not have a notion of exiting administrative mode"""
        return ""

    def config_mode(
        self,
        config_command: str = "edit-config exclusive",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        """Enable config edit-mode for Nokia SR OS"""
        output = ""
        if not pattern:
            pattern = rf"\(ex\)\[.*{self.base_prompt}.*$"
            re_flags = re.DOTALL
        # Only model-driven CLI supports config-mode
        if "@" in self.base_prompt:
            output += super().config_mode(
                config_command=config_command, pattern=pattern, re_flags=re_flags
            )
        return output

    def exit_config_mode(self, *args: Any, **kwargs: Any) -> str:
        """Disable config edit-mode for Nokia SR OS"""
        output = self._exit_all()
        # Model-driven CLI
        if "@" in self.base_prompt and "(ex)[" in output:
            # Asterisk indicates changes were made.
            if "*(ex)[" in output:
                log.warning("Uncommitted changes! Discarding changes!")
                output += self._discard()
            cmd = "quit-config"
            self.write_channel(self.normalize_cmd(cmd))
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(pattern=re.escape(cmd))
                output += self.read_until_prompt(read_entire_line=True)
            else:
                output += self.read_until_prompt(read_entire_line=True)
        if self.check_config_mode():
            raise ValueError("Failed to exit configuration mode")
        return output

    def check_config_mode(
        self,
        check_string: str = r"(ex)[",
        pattern: str = r"@",
        force_regex: bool = False,
    ) -> bool:
        """Check config mode for Nokia SR OS"""
        if "@" not in self.base_prompt:
            # Classical CLI
            return False
        else:
            # Model-driven CLI look for "exclusive"
            return super().check_config_mode(check_string=check_string, pattern=pattern)

    def save_config(self, *args: Any, **kwargs: Any) -> str:
        """Persist configuration to cflash for Nokia SR OS"""
        return self._send_command_str(command_string="/admin save", expect_string=r"#")

    def send_config_set(
        self,
        config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
        exit_config_mode: bool = True,
        **kwargs: Any,
    ) -> str:
        """Model driven CLI requires you not exit from configuration mode."""
        # Set to False if model-driven CLI
        if "@" in self.base_prompt:
            exit_config_mode = False
        return super().send_config_set(
            config_commands=config_commands, exit_config_mode=exit_config_mode, **kwargs
        )

    def commit(self, *args: Any, **kwargs: Any) -> str:
        """Activate changes from private candidate for Nokia SR OS"""
        output = self._exit_all()
        if "@" in self.base_prompt and "*(ex)[" in output:
            log.info("Apply uncommitted changes!")
            cmd = "commit"
            self.write_channel(self.normalize_cmd(cmd))
            new_output = ""
            if self.global_cmd_verify is not False:
                new_output += self.read_until_pattern(pattern=re.escape(cmd))
            if "@" not in new_output:
                new_output += self.read_until_pattern(r"@")
            output += new_output
        return output

    def _exit_all(self) -> str:
        """Return to the 'root' context."""
        output = ""
        exit_cmd = "exit all"
        self.write_channel(self.normalize_cmd(exit_cmd))
        # Make sure you read until you detect the command echo (avoid getting out of sync)
        if self.global_cmd_verify is not False:
            output += self.read_until_pattern(pattern=re.escape(exit_cmd))
            output += self.read_until_prompt(read_entire_line=True)
        else:
            output += self.read_until_prompt(read_entire_line=True)
        return output

    def _discard(self) -> str:
        """Discard changes from private candidate for Nokia SR OS"""
        output = ""
        if "@" in self.base_prompt:
            cmd = "discard"
            self.write_channel(self.normalize_cmd(cmd))
            new_output = ""
            if self.global_cmd_verify is not False:
                new_output += self.read_until_pattern(pattern=re.escape(cmd))
            if "@" not in new_output:
                new_output += self.read_until_prompt(read_entire_line=True)
            output += new_output
        return output

    def strip_prompt(self, *args: Any, **kwargs: Any) -> str:
        """Strip prompt from the output."""
        output = super().strip_prompt(*args, **kwargs)
        if "@" in self.base_prompt:
            # Remove Nokia context prompt too
            output_list = output.rstrip().splitlines()
            last_line = output_list[-1]
            other_lines = output_list[:-1]
            last_line = nokia_context_filter(last_line)
            output_list = other_lines + [last_line]
            return "\n".join(output_list).rstrip()
        else:
            return output

    def cleanup(self, command: str = "logout") -> None:
        """Gracefully exit the SSH session."""
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'logout'.
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)


class NokiaSrosSSH(NokiaSros):
    """Nokia SR OS SSH driver."""

    pass


class NokiaSrosTelnet(NokiaSros):
    """Nokia SR OS Telnet driver."""

    pass


class NokiaSrosFileTransfer(BaseFileTransfer):
    def __init__(
        self,
        ssh_conn: BaseConnection,
        source_file: str,
        dest_file: str,
        file_system: Optional[str] = None,
        direction: str = "put",
        socket_timeout: float = 10.0,
        progress: Optional[Callable[..., Any]] = None,
        progress4: Optional[Callable[..., Any]] = None,
        hash_supported: bool = False,
    ) -> None:
        super().__init__(
            ssh_conn=ssh_conn,
            source_file=source_file,
            dest_file=dest_file,
            file_system=file_system,
            direction=direction,
            socket_timeout=socket_timeout,
            progress=progress,
            progress4=progress4,
            hash_supported=hash_supported,
        )

    def _file_cmd_prefix(self) -> str:
        """
        Allow MD-CLI to execute file operations by using classical CLI.

        Returns "//" if the current prompt is MD-CLI (empty string otherwise).
        """
        return "//" if "@" in self.ssh_ctl_chan.base_prompt else ""

    def remote_space_available(
        self, search_pattern: str = r"(\d+)\s+\w+\s+free"
    ) -> int:
        """Return space available on remote device."""

        # Sample text for search_pattern.
        # "               3 Dir(s)               961531904 bytes free."
        remote_cmd = self._file_cmd_prefix() + "file dir {}".format(self.file_system)
        remote_output = self.ssh_ctl_chan._send_command_str(remote_cmd)
        match = re.search(search_pattern, remote_output)
        assert match is not None
        return int(match.group(1))

    def check_file_exists(self, remote_cmd: str = "") -> bool:
        """Check if destination file exists (returns boolean)."""

        if self.direction == "put":
            if not remote_cmd:
                remote_cmd = self._file_cmd_prefix() + "file dir {}/{}".format(
                    self.file_system, self.dest_file
                )
            dest_file_name = self.dest_file.replace("\\", "/").split("/")[-1]
            remote_out = self.ssh_ctl_chan.send_command(remote_cmd)
            if "File Not Found" in remote_out:
                return False
            elif dest_file_name in remote_out:
                return True
            else:
                raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == "get":
            return os.path.exists(self.dest_file)
        else:
            raise ValueError("Unexpected value for self.direction")

    def remote_file_size(
        self, remote_cmd: str = "", remote_file: Optional[str] = None
    ) -> int:
        """Get the file size of the remote file."""

        if remote_file is None:
            if self.direction == "put":
                remote_file = self.dest_file
            elif self.direction == "get":
                remote_file = self.source_file
            else:
                raise ValueError("Unexpected value for self.direction")
        if not remote_cmd:
            remote_cmd = self._file_cmd_prefix() + "file dir {}/{}".format(
                self.file_system, remote_file
            )
        remote_out = self.ssh_ctl_chan._send_command_str(remote_cmd)

        if "File Not Found" in remote_out:
            raise IOError("Unable to find file on remote system")

        dest_file_name = remote_file.replace("\\", "/").split("/")[-1]
        # Parse dir output for filename. Output format is:
        # "10/16/2019  10:00p                6738 {dest_file_name}"

        pattern = r"\S+\s+\S+\s+(\d+)\s+{}".format(re.escape(dest_file_name))
        match = re.search(pattern, remote_out)

        if not match:
            raise ValueError("Filename entry not found in dir output")

        file_size = int(match.group(1))
        return file_size

    def verify_file(self) -> bool:
        """Verify the file has been transferred correctly based on filesize."""
        if self.direction == "put":
            return os.stat(self.source_file).st_size == self.remote_file_size(
                remote_file=self.dest_file
            )
        elif self.direction == "get":
            return (
                self.remote_file_size(remote_file=self.source_file)
                == os.stat(self.dest_file).st_size
            )
        else:
            raise ValueError("Unexpected value of self.direction")

    def file_md5(self, file_name: str, add_newline: bool = False) -> str:
        raise AttributeError("SR-OS does not support an MD5-hash operation.")

    @staticmethod
    def process_md5(md5_output: str, pattern: str = "") -> str:
        raise AttributeError("SR-OS does not support an MD5-hash operation.")

    def compare_md5(self) -> bool:
        raise AttributeError("SR-OS does not support an MD5-hash operation.")

    def remote_md5(self, base_cmd: str = "", remote_file: Optional[str] = None) -> str:
        raise AttributeError("SR-OS does not support an MD5-hash operation.")
