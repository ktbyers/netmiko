import paramiko
import re
import time
from typing import Optional

from netmiko.base_connection import BaseConnection
from netmiko import log
from netmiko.exceptions import (
	NetmikoTimeoutException,
	NetmikoAuthenticationException,
	ConfigInvalidException,
)


class FortinetSSH(BaseConnection):
	def _modify_connection_params(self) -> None:
		"""Modify connection parameters prior to SSH connection."""
		paramiko_transport = getattr(paramiko, "Transport")
		paramiko_transport._preferred_kex = (
			"diffie-hellman-group14-sha1",
			"diffie-hellman-group-exchange-sha1",
			"diffie-hellman-group-exchange-sha256",
			"diffie-hellman-group1-sha1",
		)

	def session_preparation(self) -> None:
		"""Prepare the session after the connection has been established."""

		data = self._test_channel_read(pattern="to accept|[#$]")
		# If "set post-login-banner enable" is set it will require you to press 'a'
		# to accept the banner before you login. This will accept if it occurs
		if "to accept" in data:
			self.write_channel("a\r")
			self._test_channel_read(pattern=r"[#$]")

		self.set_base_prompt(alt_prompt_terminator="$")
		self.disable_paging()
		self.clear_buffer()

	def set_base_prompt(self, 
		pri_prompt_terminator="#", 
		alt_prompt_terminator="$", 
		delay_factor=1.0,
		pattern = r"(#|\$)"
		):
		"""Sets self.base_prompt

		Used as delimiter for stripping of trailing prompt in output.

		Should be set to something that is general and applies in multiple contexts. For Cisco
		devices this will be set to router hostname (i.e. prompt without > or #).

		This will be set on entering user exec or privileged exec on Cisco, but not when
		entering/exiting config mode.

		:param pri_prompt_terminator: Primary trailing delimiter for identifying a device prompt

		:param alt_prompt_terminator: Alternate trailing delimiter for identifying a device prompt

		:param delay_factor: See __init__: global_delay_factor

		:param pattern: Regular expression pattern to search for in find_prompt() call
		"""
		
		return super().set_base_prompt(
			pri_prompt_terminator=pri_prompt_terminator, 
			alt_prompt_terminator=alt_prompt_terminator,
			delay_factor=delay_factor,
			pattern = pattern
		)

	def find_prompt(
		self, 
		delay_factor: float = 1.0, 
		pattern: str = r"(#|\$)", 
		) -> str:
		"""Finds the current network device prompt, last line only.

		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int

		:param pattern: Regular expression pattern to determine whether prompt is valid

		:param confirm_pattern: Regular expression pattern to confirm prompt was found by auto discovery.
		"""
		return super().find_prompt(
			delay_factor=delay_factor, 
			pattern=pattern,
		)

	def send_config_set(
		self,
		config_commands = None,
		exit_config_mode: bool = True,
		read_timeout: float = None,
		delay_factor: float = 1.0,
		max_loops: int = 150,
		strip_prompt: bool = False,
		strip_command: bool = False,
		config_mode_command: str = None,
		cmd_verify: bool = True,
		enter_config_mode: bool = False,
		error_pattern: str = "",
		terminator: str = r"",
		bypass_commands: str = None,
		) -> str:
		"""
		Send configuration commands down the SSH channel.

		config_commands is an iterable containing all of the configuration commands.
		The commands will be executed one after the other.

		Automatically exits/enters configuration mode.

		:param config_commands: Multiple configuration commands to be sent to the device

		:param exit_config_mode: Determines whether or not to exit config mode after complete

		:param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

		:param max_loops: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

		:param strip_prompt: Determines whether or not to strip the prompt

		:param strip_command: Determines whether or not to strip the command

		:param read_timeout: Absolute timer to send to read_channel_timing. Should be rarely needed.

		:param config_mode_command: The command to enter into config mode

		:param cmd_verify: Whether or not to verify command echo for each command in config_set

		:param enter_config_mode: Do you enter config mode before sending config commands

		:param error_pattern: Regular expression pattern to detect config errors in the
		output.

		:param terminator: Regular expression pattern to use as an alternate terminator in certain
		situations.

		:param bypass_commands: Regular expression pattern indicating configuration commands
		where cmd_verify is automatically disabled.
		"""
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
			bypass_commands=bypass_commands
		)

	def enable(self, cmd="", pattern="", re_flags=re.IGNORECASE):
		"""Not Supported for this platform"""
		pass

	def exit_enable_mode(self, exit_command: str = "") -> str:
		"""Not Supported for this platform"""
		pass

	def set_terminal_width(self):
		"""Not Supported for this platform"""
		pass

	def check_config_mode(
		self, 
		check_string: str = r"(\) #|\) \$)", 
		pattern: str = r"", 
		force_regex: bool = True
		) -> bool:
		"""Checks if the device is in configuration mode or not.

		:param check_string: Identification of configuration mode from the device
		:type check_string: str

		:param pattern: Pattern to terminate reading of channel
		:type pattern: str
		"""
		return super().check_config_mode(
			check_string=check_string, pattern=pattern, force_regex=force_regex
		)

	def exit_config_mode(self, exit_config="end", pattern=r"(#|\$)"):
		"""Exit from configuration mode.

		:param exit_config: Command to exit configuration mode
		:type exit_config: str

		:param pattern: Pattern to terminate reading of channel
		:type pattern: str
		"""
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
		"""Disable paging is only available with specific roles so it may fail.

		:param command: Device command to disable pagination of output

		:param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.
		"""

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
