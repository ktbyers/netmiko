from __future__ import unicode_literals
from netmiko.base_connection import BaseConnection
from netmiko import log
from netmiko.exceptions import (
	NetmikoTimeoutException,
	NetmikoAuthenticationException,
	ConfigInvalidException,
)
import time
import re


class AudiocodeBaseSSH (BaseConnection):
	"""Common Methods for AudioCodes running 7.2 CLI for SSH."""

	def session_preparation(self):
		"""Prepare the session after the connection has been established."""
		self._test_channel_read(pattern=r"[>#]")
		self.set_base_prompt()
		self.disable_paging()
		self.set_terminal_width()
		# Clear the read buffer
		self.clear_buffer()

	def set_base_prompt(self, 
		pri_prompt_terminator="#", 
		alt_prompt_terminator=">", 
		delay_factor=1.0,
		pattern = "(\*?#|\*?>)$"
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
		
		return super(AudiocodeBaseSSH, self).set_base_prompt(
			pri_prompt_terminator=pri_prompt_terminator, 
			alt_prompt_terminator=alt_prompt_terminator,
			delay_factor=delay_factor,
			pattern = pattern
		)

	def find_prompt(self, 
		delay_factor = 1.0, 
		max_loops = 10, 
		pattern = None):
		"""Finds the current network device prompt, last line only.

		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int

		:param pattern: Regular expression pattern to determine whether prompt is valid
		"""
		delay_factor = self.select_delay_factor(delay_factor)
		self.clear_buffer()
		self.write_channel(self.RETURN)
		sleep_time = delay_factor * 0.1
		time.sleep(sleep_time)

		# Created parent loop to counter wrong prompts due to spamming alarm logs into terminal.
		max_loops = max_loops
		loops = 0
		while loops <= max_loops:
			# Initial attempt to get prompt
			prompt = self.read_channel().strip()
			count = 0
			while count <= 12 and not prompt:
				prompt = self.read_channel().strip()
				if not prompt:
					self.write_channel(self.RETURN)
					time.sleep(sleep_time)
					if sleep_time <= 3:
						# Double the sleep_time when it is small
						sleep_time *= 2
					else:
						sleep_time += 1
				count += 1

			# If multiple lines in the output take the last line
			prompt = prompt.split(self.RESPONSE_RETURN)[-1]
			prompt = prompt.strip()
			self.clear_buffer()

			# This verifies a valid prompt has been found before proceeding.
			if pattern:
				if re.search(pattern, prompt):
					break
			elif not prompt and (max_loops - 1):
				raise ValueError(f"Unable to find prompt: {prompt}")
			
			self.write_channel(self.RETURN)
			loops += 1
			time.sleep(1)

		log.debug(f"[find_prompt()]: prompt is {prompt}")
		return prompt

	def check_config_mode(self, 
		check_string: str = r"(\)#|\)\*#)", 
		pattern: str = "#", 
		force_regex: bool = True
		) -> bool:
		"""Checks if the device is in configuration mode or not.

		:param check_string: Identification of configuration mode from the device
		:type check_string: str

		:param pattern: Pattern to terminate reading of channel
		:type pattern: str
		"""
		return super(AudiocodeBaseSSH, self).check_config_mode(
			check_string=check_string, pattern=pattern, force_regex=force_regex
		)

	def check_enable_mode(self, check_string="#"):
		"""Check if in enable mode. Return boolean.

		:param check_string: Identification of privilege mode from device
		:type check_string: str
		"""
		return super(AudiocodeBaseSSH, self).check_enable_mode(
			check_string=check_string
		)

	def cleanup(self):
		"""Gracefully exit the SSH session."""
		try:
			self.exit_config_mode()
		except Exception:
			pass
		# Always try to send final 'exit' regardless of whether exit_config_mode works or not.
		self._session_log_fin = True
		self.write_channel("exit" + self.RETURN)

	def enable(self,
		cmd: str = "enable",
		pattern: str = "ssword",
		enable_pattern: str = "#",
		re_flags: int = re.IGNORECASE,
		) -> str:
		"""Enter enable mode.

		:param cmd: Device command to enter enable mode

		:param pattern: pattern to search for indicating device is waiting for password

		:param enable_pattern: pattern indicating you have entered enable mode

		:param re_flags: Regular expression flags used in conjunction with pattern
		"""
		return super(AudiocodeBaseSSH, self).enable(
			cmd=cmd, pattern=pattern, enable_pattern=enable_pattern, re_flags=re_flags
		)

	def exit_config_mode(self, exit_config="exit", pattern="#"):
		"""Exit from configuration mode.

		:param exit_config: Command to exit configuration mode
		:type exit_config: str

		:param pattern: Pattern to terminate reading of channel
		:type pattern: str
		"""
		return super(AudiocodeBaseSSH, self).exit_config_mode(
			exit_config=exit_config, pattern=pattern
		)

	def exit_enable_mode(self, exit_command="disable"):
		"""Exit enable mode.

		:param exit_command: Command that exits the session from privileged mode
		:type exit_command: str
		"""
		return super(AudiocodeBaseSSH, self).exit_enable_mode(
			exit_command=exit_command
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
		cmd_verify: bool = False,
		enter_config_mode: bool = False,
		error_pattern: str = "",
		terminator: str = r"\*?#",
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
		if self.global_cmd_verify is not None:
			cmd_verify = self.global_cmd_verify

		if delay_factor is not None or max_loops is not None:
			#warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

			# Calculate an equivalent read_timeout (if using old settings)
			# Eliminate in Netmiko 5.x
			if read_timeout is None:
				max_loops = 150 if max_loops is None else max_loops
				delay_factor = 1.0 if delay_factor is None else delay_factor

				# If delay_factor has been set, then look at global_delay_factor
				delay_factor = self.select_delay_factor(delay_factor)

				#read_timeout = calc_old_timeout(
				#	max_loops=max_loops, delay_factor=delay_factor, loop_delay=0.1
				#)

		if delay_factor is None:
			delay_factor = self.select_delay_factor(0)
		else:
			delay_factor = self.select_delay_factor(delay_factor)

		if read_timeout is None:
			read_timeout = 15
		else:
			read_timeout = read_timeout

		if config_commands is None:
			return ""
		elif isinstance(config_commands, str):
			config_commands = (config_commands,)

		if not hasattr(config_commands, "__iter__"):
			raise ValueError("Invalid argument passed into send_config_set")

		if bypass_commands is None:
			# Commands where cmd_verify is automatically disabled reg-ex logical-or
			bypass_commands = r"^banner .*$"

		# Set bypass_commands="" to force no-bypass (usually for testing)
		bypass_detected = False
		if bypass_commands:
			bypass_detected = any(
				[True for cmd in config_commands if re.search(bypass_commands, cmd)]
			)
		if bypass_detected:
			cmd_verify = False

		# Send config commands
		output = ""
		if enter_config_mode:
			if config_mode_command:
				output += self.config_mode(config_mode_command)
			else:
				output += self.config_mode()

		# Perform output gathering line-by-line (legacy way)
		if self.fast_cli and self._legacy_mode and not error_pattern:
			for cmd in config_commands:
				self.write_channel(self.normalize_cmd(cmd))
			# Gather output
			output += self.read_channel_timing(read_timeout=read_timeout)

		elif not cmd_verify:
			for cmd in config_commands:
				self.write_channel(self.normalize_cmd(cmd))
				time.sleep(delay_factor * 0.05)

				# Gather the output incrementally due to error_pattern requirements
				if error_pattern:
					output += self.read_channel_timing(read_timeout=read_timeout)
					if re.search(error_pattern, output, flags=re.M):
						msg = f"Invalid input detected at command: {cmd}"
						raise ConfigInvalidException(msg)

			# Standard output gathering (no error_pattern) - modified because read_timeout was causing it to fail.
			if not error_pattern:
				output += self.read_channel_timing(delay_factor=delay_factor,max_loops=max_loops)

		else:
			for cmd in config_commands:
				self.write_channel(self.normalize_cmd(cmd))

				# Make sure command is echoed
				output += self.read_until_pattern(pattern=re.escape(cmd.strip()))

				# Read until next prompt or terminator (#); the .*$ forces read of entire line
				pattern = f"(?:{re.escape(self.base_prompt)}.*$|{terminator}.*$)"
				output += self.read_until_pattern(pattern=pattern, re_flags=re.M)

				if error_pattern:
					if re.search(error_pattern, output, flags=re.M):
						msg = f"Invalid input detected at command: {cmd}"
						raise ConfigInvalidException(msg)

		if exit_config_mode:
			output += self.exit_config_mode()
		output = self._sanitize_output(output)
		log.debug(f"{output}")
		return output

	def disable_paging(
		self, 
		disable_window_config = ["config system","cli-settings","window-height 0","exit"],
		delay_factor=.5
		):
		"""This is designed to disable window paging which prevents paged command 
		output from breaking the script.
		
		:param disable_window_config: Command, or list of commands, to execute.
		:type disable_window_config: str
		
		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int
		
		"""
		self.enable()
		delay_factor = self.select_delay_factor(delay_factor)
		time.sleep(delay_factor * 0.1)
		self.clear_buffer()
		disable_window_config = disable_window_config
		log.debug("In disable_paging")
		self.send_config_set(disable_window_config,True,.25,150,False,False,None,False,False)
		log.debug("Exiting disable_paging")

	def _enable_paging(
		self, 
		enable_window_config = ["config system","cli-settings","window-height automatic","exit"],
		delay_factor=.5
		):
		"""This is designed to reenable window paging.
		
		:param enable_window_config: Command, or list of commands, to execute.
		:type enable_window_config: str
		
		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int
		
		"""
		self.enable()
		delay_factor = self.select_delay_factor(delay_factor)
		time.sleep(delay_factor * 0.1)
		self.clear_buffer()
		enable_window_config = enable_window_config
		log.debug("In _enable_paging")
		self.send_config_set(enable_window_config,True,.25,150,False,False,None,False,False)
		log.debug("Exiting _enable_paging")

	def save_config(self, cmd="write", confirm=False, confirm_response=""):
		"""Saves the running configuration.
		
		:param cmd: Command to save configuration
		:type cmd: str
		
		:param confirm: Command if confirmation prompt is required
		:type confirm: bool

		:param confirm_response: Command if confirm response required to further script
		:type confirm response: str
		
		"""
		self.enable()
		if confirm:
			output = self.send_command_timing(command_string=cmd)
			if confirm_response:
				output += self.send_command_timing(confirm_response)
			else:
				# Send enter by default
				output += self.send_command_timing(self.RETURN)
		else:
			# Some devices are slow so match on trailing-prompt if you can
			output = self.send_command(command_string=cmd)
		return (output)
		
	def _reload_device(self, reload_device=True, reload_save=True, cmd_save="reload now", cmd_no_save="reload without-saving"):
		"""Reloads the device.
		
		:param reload_device: Boolean to determine if reload should occur.
		:type reload_device: bool
		
		:param reload_device: Boolean to determine if reload with saving first should occur.
		:type reload_device: bool
		
		:param cmd_save: Command to reload device with save.  Options are "reload now" and "reload if-needed".
		:type cmd_save: str
		
		:param cmd_no_save: Command to reload device.  Options are "reload without-saving", "reload without-saving in [minutes]".
		:type cmd_no_save: str

		"""
		self.enable()
		if reload_device == True and reload_save == True:
			self._enable_paging()
			output = self.send_command_timing(command_string=cmd_save)
			try:
				self.cleanup()
			except:
				pass
		elif reload_device == True and reload_save == False:
			output = self.send_command_timing(command_string=cmd_no_save)
			try:
				self.cleanup()
			except:
				pass
		else:
			output = "***Reload not performed***"
		return (output)			

	def _device_terminal_exit(self, command="exit"):
		"""This is for accessing devices via terminal. It first reenables window paging for
		future use and exits the device before you send the disconnect method"""
		
		self.enable()
		self._enable_paging()
		output = self.send_command_timing(command)
		log.debug("_device_terminal_exit executed")
		return (output)

	def set_terminal_width(self):
		"""Not a configurable parameter"""
		pass


class AudiocodeBaseTelnet(AudiocodeBaseSSH):
	"""Audiocode Telnet driver."""
	pass

	
class Audiocode66SSH(AudiocodeBaseSSH):
	"""Audiocode this applies to 6.6 Audiocode Firmware versions."""

	def disable_paging(
		self, 
		disable_window_config = ["config system","cli-terminal","set window-height 0","exit"],
		delay_factor=.5
		):
		"""This is designed to disable window paging which prevents paged command 
		output from breaking the script.
				
		:param disable_window_config: Command, or list of commands, to execute.
		:type disable_window_config: str
			
		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int
		
		"""		
		return super(Audiocode66SSH, self).disable_paging(
			disable_window_config=disable_window_config, delay_factor=delay_factor
		)
		
	def _enable_paging(
		self, 
		enable_window_config = ["config system","cli-terminal","set window-height 100","exit"],
		delay_factor=.5
		):
		"""This is designed to reenable window paging
		
		:param enable_window_config: Command, or list of commands, to execute.
		:type enable_window_config: str
		
		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int
		
		"""
		return super(Audiocode66SSH, self)._enable_paging(
			enable_window_config=enable_window_config, delay_factor=delay_factor
		)


class Audiocode66Telnet(Audiocode66SSH):
	"""Audiocode Telnet driver."""
	pass


class AudiocodeShellSSH(AudiocodeBaseSSH):
	"""Audiocode this applies to 6.6 Audiocode Firmware versions that only use the Shell."""
	def session_preparation(self):
		"""Prepare the session after the connection has been established."""
		self.write_channel(self.RETURN)
		self.write_channel(self.RETURN)
		self._test_channel_read(pattern="/>")
		self.set_base_prompt()
		# Clear the read buffer
		time.sleep(0.3 * self.global_delay_factor)
		self.clear_buffer()

	def set_base_prompt(self, 
		pri_prompt_terminator="/>", 
		alt_prompt_terminator="", 
		delay_factor=1.0,
		pattern = "/>"
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
		prompt = self.find_prompt(delay_factor=delay_factor, pattern=pattern)
		pattern = pri_prompt_terminator
		if not re.search(pattern, prompt):
			raise ValueError(f"Router prompt not found: {repr(prompt)}")
		else:
			# Strip off trailing terminator
			self.base_prompt = prompt
			return self.base_prompt

	def enable(self, cmd="", pattern="", re_flags=re.IGNORECASE):
		"""Not in use"""
		pass

	def check_enable_mode(self, check_string="#"):
		"""Not in use"""
		pass

	def exit_enable_mode(self, exit_command=""):
		"""Not in use"""
		pass

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
		cmd_verify: bool = False,
		enter_config_mode: bool = False,
		error_pattern: str = "",
		terminator: str = r"/>",
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
		return super(AudiocodeShellSSH, self).send_config_set(
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

	def check_config_mode(self, 
		check_string: str = "/CONFiguration", 
		pattern: str = "", 
		force_regex: bool = False
		) -> bool:
		"""Checks if the device is in configuration mode or not.

		:param check_string: Identification of configuration mode from the device
		:type check_string: str

		:param pattern: Pattern to terminate reading of channel
		:type pattern: str
		"""
		return super(AudiocodeShellSSH, self).check_config_mode(
			check_string=check_string, pattern=pattern, force_regex=force_regex
		)

	def exit_config_mode(self, exit_config="..", pattern="/>"):
		"""Exit from configuration mode.

		:param exit_config: Command to exit configuration mode
		:type exit_config: str

		:param pattern: Pattern to terminate reading of channel
		:type pattern: str
		"""
		return super(AudiocodeShellSSH, self).exit_config_mode(
			exit_config=exit_config, pattern=pattern
		)

	def disable_paging(self):
		"""Not in use"""
		pass

	def save_config(self, 
		cmd="SaveConfiguration", 
		confirm=False,
		confirm_response=""
		):
		"""Saves the running configuration.
		
		:param cmd: Command to save configuration
		:type cmd: str
		
		:param confirm: Command if confirmation prompt is required
		:type confirm: bool

		:param confirm_response: Command if confirm response required to further script
		:type confirm response: str
		
		"""
		return super(AudiocodeShellSSH, self).save_config(
			cmd=cmd, confirm=confirm, confirm_response=confirm_response
		)
		
	def _reload_device(self, 
		reload_device=True, 
		reload_save=True, 
		cmd_save="SaveAndReset", 
		cmd_no_save="ReSetDevice",
		reload_message="Resetting the board"
		):
		"""Reloads the device.
		
		:param reload_device: Boolean to determine if reload should occur.
		:type reload_device: bool
		
		:param reload_device: Boolean to determine if reload with saving first should occur.
		:type reload_device: bool
		
		:param cmd_save: Command to reload device with save.  Options are "reload now" and "reload if-needed".
		:type cmd_save: str
		
		:param cmd_no_save: Command to reload device.  Options are "reload without-saving", "reload without-saving in [minutes]".
		:type cmd_no_save: str

		:param reload_message: This is the pattern by which the reload is detected.
		:type reload_message: str

		"""
		return super(AudiocodeShellSSH, self)._reload_device(
			reload_device=reload_device,
			reload_save=reload_save,
			cmd_save=cmd_save,
			cmd_no_save=cmd_no_save,
			reload_message=reload_message
		)

	def _device_terminal_exit(self, command="exit"):
		"""This is for accessing devices via terminal. It first reenables window paging for
		future use and exits the device before you send the disconnect method"""
		return super(AudiocodeShellSSH, self)._device_terminal_exit(
			command=command
		)

	def _enable_paging(self):
		"""Not in use"""
		pass
	
class AudiocodeShellTelnet(AudiocodeShellSSH):
	"""Audiocode this applies to 6.6 Audiocode Firmware versions that only use the Shell."""
	pass





