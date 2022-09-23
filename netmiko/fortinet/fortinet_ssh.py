import paramiko
import re
import time
from typing import Any, Optional, Sequence, Iterator, TextIO, Union, List

from netmiko.base_connection import BaseConnection
from netmiko.no_enable import NoEnable
from netmiko import log
from netmiko.exceptions import (
	NetmikoTimeoutException,
	NetmikoAuthenticationException,
	ConfigInvalidException,
)


class FortinetSSH(NoEnable, BaseConnection):
	prompt_pattern = r"[#$]"

	def _modify_connection_params(self) -> None:
		"""Modify connection parameters prior to SSH connection."""
		paramiko_transport = getattr(paramiko, "Transport")
		paramiko_transport._preferred_kex = (
			"diffie-hellman-group14-sha1",
			"diffie-hellman-group-exchange-sha1",
			"diffie-hellman-group-exchange-sha256",
			"diffie-hellman-group1-sha1",
		)

	def _try_session_preparation(self, force_data: bool = False) -> None:
		super()._try_session_preparation(force_data=force_data)

	def session_preparation(self) -> None:
		"""Prepare the session after the connection has been established."""

		data = self._test_channel_read(pattern=f"to accept|{self.prompt_pattern}")

		# If "set post-login-banner enable" is set it will require you to press 'a'
		# to accept the banner before you login. This will accept if it occurs
		if "to accept" in data:
			self.write_channel("a\r")
			self._test_channel_read(pattern=r"[#$]")

		self.set_base_prompt()
		self.disable_paging()

	def set_base_prompt(self, 
		pri_prompt_terminator="#", 
		alt_prompt_terminator="$", 
		delay_factor=1.0,
		pattern = ""
		):
		
		if not pattern:
			pattern = self.prompt_pattern

		return super().set_base_prompt(
			pri_prompt_terminator=pri_prompt_terminator, 
			alt_prompt_terminator=alt_prompt_terminator,
			delay_factor=delay_factor,
			pattern = pattern
		)

	def find_prompt(
		self, 
		delay_factor: float = 1.0, 
		pattern: str = "", 
		) -> str:

		if not pattern:
			pattern = self.prompt_pattern

		return super().find_prompt(
			delay_factor=delay_factor, 
			pattern=pattern,
		)

	def send_config_set(
		self,
		config_commands: Union[str, Sequence[str], Iterator[str], TextIO, None] = None,
		*,
		exit_config_mode: bool = True,
		read_timeout: Optional[float] = None,
		delay_factor: Optional[float] = None,
		max_loops: Optional[int] = None,
		strip_prompt: bool = False,
		strip_command: bool = False,
		config_mode_command: Optional[str] = None,
		cmd_verify: bool = True,
		enter_config_mode: bool = True,
		error_pattern: str = "",
		terminator: str = r"",
		bypass_commands: Optional[str] = None,
	) -> str:
	
		if not terminator:
			terminator = self.prompt_pattern

		if enter_config_mode and config_mode_command is None:
			msg = """
send_config_set() for the Fortinet drivers require that you specify the
config_mode_command. For example, config_mode_command="config system global".
			"""
			raise ValueError(msg)

		return super().send_config_set(
			config_commands=config_commands,
			exit_config_mode=exit_config_mode,
			read_timeout=read_timeout,
			delay_factor=delay_factor,
			max_loops=max_loops,
			strip_prompt=strip_prompt,
			strip_command=strip_command,
			config_mode_command=config_mode_command,
			cmd_verify=cmd_verify,
			enter_config_mode=enter_config_mode,
			error_pattern=error_pattern,
			terminator=terminator,
			bypass_commands=bypass_commands,
		)

	def set_terminal_width(self):
		"""Not Supported for this platform"""
		pass

	def check_config_mode(
		self, 
		check_string: str = r"(\) #|\) \$)", 
		pattern: str = r"", 
		force_regex: bool = True
		) -> bool:

		return super().check_config_mode(
			check_string=check_string, pattern=pattern, force_regex=force_regex
		)

	def exit_config_mode(self, exit_config="end", pattern=r"(#|\$)"):

		return super().exit_config_mode(
			exit_config=exit_config, pattern=pattern
		)

	def disable_paging(
		self,
		command: str = "",
		delay_factor: Optional[float] = None,
		cmd_verify: bool = True,
		pattern: Optional[str] = None,
		) -> str:

		disable_paging_commands = [
			"config global",
			"config system console",
			"set output standard",
			"end"
			]
		output = self.send_config_set(
			config_commands = disable_paging_commands,
			exit_config_mode = True,
			read_timeout = None,
			delay_factor = 1.0,
			max_loops = 150,
			enter_config_mode = False,
		)
		log.debug("***Window Paging Disabled***")
		return output

	def cleanup(self, command: str = "quit") -> None:
		"""Re-enable paging globally."""
		# Return paging state
		enable_paging_commands = ["config global", "config system console", "set output more", "end"]
		# Should test output is valid
		output = self.send_config_set(
			config_commands = enable_paging_commands,
			exit_config_mode = True,
			read_timeout = None,
			delay_factor = 1.0,
			max_loops = 150,
			enter_config_mode = False,
		)
		log.debug("***Window Paging Enabled***")

		"""Gracefully exit the SSH session."""
		try:
			self.exit_config_mode()
		except Exception:
			pass
		# Always try to send final 'exit' (command)
		self._session_log_fin = True
		self.write_channel(command + self.RETURN)

	def save_config(
		self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
		) -> str:
		"""Not Implemented, platform automatically saves"""
		raise NotImplementedError

	def _enter_global_or_vdom(self, mode_name: str = None):
		"""This allows a device enter global or vdom mode and confirm before proceeding.

		:param mode_name: the name of the mode trying to be entered: 'global', 'root' or the name of the vdom string.
		"""
		if mode_name == "global":
			log.debug("***Entering Global Mode***")
			try: 
				self.send_command(command_string="config global", expect_string=r"\(global\) # ")
			except:
				raise ValueError("Device Failed to Enter Global Mode.")
		else:
			log.debug("***Entering VDOM Mode***")
			try:
				self.send_command(command_string="config vdom", expect_string=r"\(vdom\) # ")
				self.send_command(command_string=f"edit {mode_name:}", expect_string=fr"\({mode_name}\) # ")
			except:
				raise ValueError(f"Device Failed to Enter '{mode_name}' VDOM Mode.")

	def _exit_global_or_vdom(self):
		"""This allows a device to exit global or vdom mode and confirm before proceeding"""
		mode_active = True
		log.debug("***Attempting to Exit Mode***")
		loops = 0

		while mode_active:
			output = self.find_prompt()

			if ") #" in output:
				self.write_channel("end")
			elif ") #" not in output or loops == 5:
				break

			time.sleep(1)
			loops += 1
