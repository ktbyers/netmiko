from __future__ import unicode_literals
from netmiko.base_connection import BaseConnection
from netmiko import log

import time
import re
import os
import hashlib
import io



class AudiocodeSSH (BaseConnection):
	"""Common Methods for AudioCodes running 7.2 CLI for SSH."""

	def session_preparation(self):
		"""Prepare the session after the connection has been established."""
		self._test_channel_read(pattern=r"[>#]")
		self.set_base_prompt()
		self.disable_paging()
		self.set_terminal_width()
		# Clear the read buffer
		time.sleep(0.3 * self.global_delay_factor)
		self.clear_buffer()

	def set_base_prompt(
		self, pri_prompt_terminator="#", alt_prompt_terminator=">", delay_factor=1
		):
		"""Sets self.base_prompt

		Used as delimiter for stripping of trailing prompt in output.

		Should be set to something that is general and applies in multiple contexts. For Cisco
		devices this will be set to router hostname (i.e. prompt without > or #).

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
		pattern = rf"(\*?{pri_prompt_terminator}$|\*?{alt_prompt_terminator})$"
		if not re.search(pattern, prompt):
			raise ValueError(f"Router prompt not found: {repr(prompt)}")
		else:
			# Strip off trailing terminator
			self.base_prompt = re.sub(pattern, "", prompt)
			return self.base_prompt

	def check_enable_mode(self, check_string="#"):
		"""Check if in enable mode. Return boolean.

		:param check_string: Identification of privilege mode from device
		:type check_string: str
		"""
		return super(AudiocodeSSH, self).check_enable_mode(
			check_string=check_string
		)

	def enable(self, cmd="enable", pattern="ssword", re_flags=re.IGNORECASE):
		"""Enter enable mode.

		:param cmd: Device command to enter enable mode
		:type cmd: str

		:param pattern: pattern to search for indicating device is waiting for password
		:type pattern: str

		:param re_flags: Regular expression flags used in conjunction with pattern
		:type re_flags: int
		"""
		return super(AudiocodeSSH, self).enable(
			cmd=cmd, pattern=pattern, re_flags=re_flags
		)

	def exit_enable_mode(self, exit_command="disable"):
		"""Exit enable mode.

		:param exit_command: Command that exits the session from privileged mode
		:type exit_command: str
		"""
		return super(AudiocodeSSH, self).exit_enable_mode(
			exit_command=exit_command
		)

	def check_config_mode(self, check_string=")#", pattern="#"):
		"""Checks if the device is in configuration mode or not.

		:param check_string: Identification of configuration mode from the device
		:type check_string: str

		:param pattern: Pattern to terminate reading of channel
		:type pattern: str
		"""
		self.write_channel(self.RETURN)
		# If the first check_string value is not valid, it applies the second.

		if not pattern:
			output = self._read_channel_timing(3)
		else:
			output = self.read_until_pattern(pattern=pattern)

		if check_string in output:
			return check_string in output
		else:
			check_string = ")*#"
			return check_string in output
			
	def send_config_set(
		self,
		config_commands=None,
		exit_config_mode=True,
		delay_factor=1,
		max_loops=150,
		strip_prompt=False,
		strip_command=False,
		config_mode_command=None,
		cmd_verify=True,
		enter_config_mode=True
	):
		if config_mode_command == None and enter_config_mode == True:
			raise ValueError("For this driver config_mode_command must be specified")
	
		else:
			return super(AudiocodeSSH, self).send_config_set(
				config_commands=config_commands,
				exit_config_mode=exit_config_mode,
				delay_factor=delay_factor,
				max_loops=max_loops,
				strip_prompt=strip_prompt,
				strip_command=strip_command,
				config_mode_command=config_mode_command,
				cmd_verify=cmd_verify,
				enter_config_mode=enter_config_mode
			)

	def exit_config_mode(self, exit_config="exit", pattern="#"):
		"""Exit from configuration mode.

		:param exit_config: Command to exit configuration mode
		:type exit_config: str

		:param pattern: Pattern to terminate reading of channel
		:type pattern: str
		"""
		output = ""
		if self.check_config_mode():
			self.write_channel(self.normalize_cmd(exit_config))
			output = self.read_until_pattern(pattern=pattern)
			if self.check_config_mode():
				raise ValueError("Failed to exit configuration mode")
		log.debug("exit_config_mode: {}".format(output))
		return output
	
	def cleanup(self):
		"""Gracefully exit the SSH session."""
		try:
			self.exit_config_mode()
		except Exception:
			pass
		# Always try to send final 'exit' regardless of whether exit_config_mode works or not.
		self._session_log_fin = True
		self.write_channel("exit" + self.RETURN)

	def disable_paging(
		self, 
		disable_window_config = ["cli-settings","window-height 0","exit"],
		config_mode = "config system",
		delay_factor=.5
	):
		"""This is designed to disable window paging which prevents paged command 
		output from breaking the script.
		
		:param disable_window_config: Command, or list of commands, to execute.
		:type disable_window_config: str
		
		:param config_mode: Configuration mode in which commands should be executed.
		:type config_mode: str
		
		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int
		
		"""
		
		self.enable()
		delay_factor = self.select_delay_factor(delay_factor)
		config_mode = config_mode
		time.sleep(delay_factor * 0.1)
		self.clear_buffer()
		disable_window_config = disable_window_config
		log.debug("In disable_paging")
		log.debug(f"Commands: {disable_window_config}")
		self.send_config_set(disable_window_config,True,.25,150,False,False,config_mode)
		log.debug("Exiting disable_paging")

		
	def _enable_paging(
		self, 
		enable_window_config = ["cli-settings","window-height automatic","exit"],
		config_mode = "config system",
		delay_factor=.5
	):
		"""This is designed to reenable window paging.
		
		:param enable_window_config: Command, or list of commands, to execute.
		:type enable_window_config: str
		
		:param config_mode: Configuration mode in which commands should be executed.
		:type config_mode: str
		
		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int
		
		"""
		self.enable()
		delay_factor = self.select_delay_factor(delay_factor)
		config_mode = config_mode
		time.sleep(delay_factor * 0.1)
		self.clear_buffer()
		enable_window_config = enable_window_config
		log.debug("In _enable_paging")
		log.debug(f"Commands: {enable_window_config}")
		self.send_config_set(enable_window_config,True,.25,150,False,False,config_mode)
		log.debug("Exiting _enable_paging")

	def _save_config(self, cmd="write", confirm=False, confirm_response=""):
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
		reload_device = reload_device
		reload_save = reload_save
		cmd_save = cmd_save
		cmd_no_save = cmd_no_save
		self.enable()
		
		if reload_device == True and reload_save == True:
			self._enable_paging()
			output = self.send_command(command_string=cmd_save)		
		elif reload_device == True and reload_save == False:
			output = self.send_command(command_string=cmd_no_save)
		else:
			output = "***Reload not performed***"
		
		return (output)			


	def _device_terminal_exit(self):
		"""This is for accessing devices via terminal. It first reenables window paging for
		future use and exits the device before you send the disconnect method"""
		
		self.enable()
		self._enable_paging()
		output = self.send_command_timing('exit')
		return (output)

	def set_terminal_width(self):
		"""Not a configurable parameter"""
		pass





class AudiocodeTelnet(AudiocodeSSH):
	"""Audiocode Telnet driver."""
	
	pass

	
	
	
class AudiocodeOldCLI(AudiocodeSSH):
	"""Audiocode Old CLI driver.  Common Methods that differentiate between 6.6 and the 7.2 CLI versions."""

	def disable_paging(
		self, 
		disable_window_config = ["cli-terminal","set window-height 0","exit"],
		config_mode = "config system",
		delay_factor=.5
	):
		"""This is designed to disable window paging which prevents paged command 
		output from breaking the script.
				
		:param disable_window_config: Command, or list of commands, to execute.
		:type disable_window_config: str
		
		:param config_mode: Configuration mode in which commands should be executed.
		:type config_mode: str
		
		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int
		
		"""		
		return super(AudiocodeOldCLI, self).disable_paging(
			disable_window_config=disable_window_config, config_mode=config_mode, delay_factor=delay_factor
		)

			
	def _enable_paging(
		self, 
		enable_window_config = ["cli-terminal","set window-height 100","exit"],
		config_mode = "config system",
		delay_factor=.5
	):
		"""This is designed to reenable window paging
		
		:param enable_window_config: Command, or list of commands, to execute.
		:type enable_window_config: str
		
		:param config_mode: Configuration mode in which commands should be executed.
		:type config_mode: str
		
		:param delay_factor: See __init__: global_delay_factor
		:type delay_factor: int
		
		"""
		return super(AudiocodeOldCLI, self)._enable_paging(
			enable_window_config=enable_window_config, config_mode=config_mode, delay_factor=delay_factor
		)




