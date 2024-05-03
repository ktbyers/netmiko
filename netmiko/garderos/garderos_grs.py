from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import ConfigInvalidException
from time import sleep
from typing import (
    Optional,
    Any,
    List,
    Dict,
    Sequence,
    Iterator,
    TextIO,
    Union,
)


class GarderosGrsSSH(CiscoSSHConnection):
    def session_preparation(self) -> None:
        """Prepare the session after the connection has been established"""
        self.ansi_escape_codes = True
        self._test_channel_read()
        self.set_base_prompt(pri_prompt_terminator="#")
        self.clear_buffer()

    def send_command(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """Add strip() command to output of send_command()"""

        # First check if command contains a newline/carriage-return.
        # This is not allowed in Garderos GRS
        command_string = args[0] if args else kwargs["command_string"]
        if "\n" in command_string or "\r" in command_string:
            raise ValueError(
                f"The command contains an illegal newline/carriage-return: {command_string}"
            )

        # Send command to device
        result = super().send_command(*args, **kwargs)

        # Optimize output of strings
        if isinstance(result, str):
            result = result.strip()
        return result

    def check_config_mode(
        self, check_string: str = ")#", pattern: str = "#", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(
            check_string=check_string, pattern=pattern, force_regex=force_regex
        )

    def config_mode(
        self,
        config_command: str = "configuration terminal",
        pattern: str = "",
        re_flags: int = 0,
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = "#") -> str:
        """Exit from configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def commit(self, commit: str = "commit") -> str:
        """Commit the candidate configuration."""

        if self.check_config_mode():
            raise ValueError("Device is in configuration mode. Please exit first.")

        # Run commit command
        commit_result = self._send_command_str(commit)

        # Verify success
        if "No configuration to commit" in commit_result:
            raise ValueError(
                "No configuration to commit. Please configure device first."
            )
        elif "Values will be reloaded" not in commit_result:
            raise ValueError(f"Commit was unsuccessful. Device said: {commit_result}")

        # Garderos needs a second to apply the config
        # If the "show configuration running" command is executed to quickly after committing
        # it will result in error "No running configuration found."
        sleep(1)
        return commit_result

   def save_config(
        self,
        cmd: str = "write startup-configuration",
        confirm: bool = False,
        confirm_response: str = "",
    ) -> str:
        """Saves Config."""

        if self.check_config_mode():
            raise ValueError("Device is in configuration mode. Please exit first.")

        if confirm:
            raise ValueError(
                "Garderos saves the config without the need of confirmation. "
                "Please set variable 'confirm' to False!"
            )

        save_config_result = self._send_command_str(cmd)

        # Verify success
        if "Values are persistently saved to STARTUP-CONF" not in save_config_result:
            raise ValueError(
                f"Saving configuration was unsuccessful. Device said: {save_config_result}"
            )

        return save_config_result

    def check_linux_mode(self, check_string: str = "]#", pattern: str = "#") -> bool:
        """Checks if the device is in Linux mode or not.

        :param check_string: Identification of configuration mode from the device

        :param pattern: Pattern to terminate reading of channel
        """
        self.write_channel(self.RETURN)
        output = self.read_until_prompt(read_entire_line=True)
        return check_string in output

    def linux_mode(self, linux_command: str = "linux-shell", pattern: str = "") -> str:
        """Enter into Linux mode.

        :param config_command: Linux command to send to the device

        :param pattern: Pattern to terminate reading of channel
        """
        output = ""
        if not self.check_linux_mode():
            self.write_channel(self.normalize_cmd(linux_command))
            output = self.read_until_pattern(pattern=pattern)
            if not self.check_linux_mode():
                raise ValueError("Failed to enter Linux mode.")
        return output

    def exit_linux_mode(self, exit_linux: str = "exit", pattern: str = "#") -> str:
        """Exit from Linux mode.

        :param exit_config: Command to exit Linux mode

        :param pattern: Pattern to terminate reading of channel
        """
        output = ""
        if self.check_linux_mode():
            self.write_channel(self.normalize_cmd(exit_linux))
            output = self.read_until_pattern(pattern=pattern)
            if self.check_linux_mode():
                raise ValueError("Failed to exit Linux mode")
        return output

    def remove_and_replace_control_chars(self, s: str) -> str:
        """Removing all occurrences of "\r\n\r" except of the last occurrence
        Last occurence will be replaced by "\n"

        :param s: String that needs to be cleansed
        """
        # Because the sequence "\r\n\r" also matches "\r\n\r\n",
        # we need to replace "\r\n\r\n" with "\n\n" first
        s = s.replace("\r\n\r\n", "\n\n")
        # Now we have eliminated "\r\n\r\n"
        # and can begin working on the remaining "\r\n\r" occurrences
        control_seq = "\r\n\r"
        if s.count(control_seq) == 0:
            return s
        else:
            index_last_occurrence = s.rfind(control_seq)
            index_rest_of_string = index_last_occurrence + len(control_seq)
            return (
                s[:index_last_occurrence].replace(control_seq, "")
                + "\n"
                + s[index_rest_of_string:]
            )

    def normalize_linefeeds(self, a_string: str) -> str:
        """Optimised normalisation of line feeds

        :param a_string: A string that may have non-normalized line feeds
            i.e. output returned from device, or a device prompt
        """
        # Garderos has special behavior in terms of line feeds:
        # The echo of commands sometimes contains "\r\n\r"
        # which breaks the functionality of _sanitize_output().
        # Therefore, this character sequence needs to be fixed
        # before passing the string to normalize_linefeeds().

        # First we will remove all the occurrences of "\r\n\r" except of the last one.
        # The last occurrence will be replaced by "\r\n".
        a_string = self.remove_and_replace_control_chars(a_string)

        # Then we will pass the string to normalize_linefeeds() to replace all line feeds with "\n"
        return super().normalize_linefeeds(a_string=a_string)

    def send_config_command(
        self,
        command_string: str,
        expect_string: Optional[str] = None,
        read_timeout: float = 10.0,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        auto_find_prompt: bool = True,
        strip_prompt: bool = True,
        strip_command: bool = True,
        normalize: bool = True,
        use_textfsm: bool = False,
        textfsm_template: Optional[str] = None,
        use_ttp: bool = False,
        ttp_template: Optional[str] = None,
        use_genie: bool = False,
        cmd_verify: bool = True,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """
        Execute a command in configuration mode and raise error if command execution failed.
        Function neither checks if device is configuration mode nor turns on configuration mode.
        """
        # Send command to device
        command_result = self.send_command(
            command_string=command_string,
            expect_string=expect_string,
            read_timeout=read_timeout,
            delay_factor=delay_factor,
            max_loops=max_loops,
            auto_find_prompt=auto_find_prompt,
            strip_prompt=strip_prompt,
            strip_command=strip_command,
            normalize=normalize,
            use_textfsm=use_textfsm,
            textfsm_template=textfsm_template,
            use_ttp=use_ttp,
            ttp_template=ttp_template,
            use_genie=use_genie,
            cmd_verify=cmd_verify,
        )
        # Verify if configuration command executed successfully
        if command_result != "Set.":
            raise ConfigInvalidException(
                'Error executing configuration command "{}". Device said: {}'.format(
                    command_string, command_result
                )
            )
        return command_result

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
        terminator: str = r"#",
        bypass_commands: Optional[str] = None,
    ) -> str:
        """
        Optimised version of send_config_set() for Garderos.
        Checks whether single config commands executed successfully.

        Automatically exits/enters configuration mode.

        :param config_commands: Multiple configuration commands to be sent to the device

        :param exit_config_mode: Determines whether or not to exit config mode after complete

        :param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        :param max_loops: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        :param strip_prompt: Determines whether or not to strip the prompt

        :param strip_command: Determines whether or not to strip the command

        :param read_timeout: Absolute timer to send to read_channel_timing. Also adjusts
        read_timeout in read_until_pattern calls.

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
        # The result of all commands will be collected to config_results
        config_results = ""
        # Set delay_factor to given value
        if delay_factor is None:
            delay_factor = self.select_delay_factor(0)
        else:
            delay_factor = self.select_delay_factor(delay_factor)
        # Verify if config_commands is an array
        if config_commands is None:
            return config_results
        elif isinstance(config_commands, str):
            config_commands = (config_commands,)
        if not hasattr(config_commands, "__iter__"):
            raise ValueError("Invalid argument passed into send_config_set")
        # Go to config mode. Use given config_mode_command if necessary.
        if enter_config_mode:
            if config_mode_command:
                config_results += self.config_mode(config_mode_command)
            else:
                config_results += self.config_mode()
        # Send all commands to the router and verify their successful execution
        for command in config_commands:
            # Verification is done in send_config_command() function
            # Will raise error on execution failure
            result = self.send_config_command(command)
            config_results = f"{command}\n{result}\n"
        # Exit config mode if needed
        if exit_config_mode:
            self.exit_config_mode()
        # Return all results
        # Will only be executed if no error occured
        return config_results

    def ssh_connect(
        self,
        host: str,
        username: str = "",
        password: str = "",
        timeout: int = 5,
        expect_prompt: str = "#",
    ) -> str:
        """
        Opening a nested SSH connection to another device

        :param host: IP address (or hostname if DNS is configured)

        :param username: Username to be used for SSH connection

        :param password: Password to be used for SSH connection

        :param timeout: Maximum time in seconds to wait for username and password prompt

        :param expect_prompt: Device prompt (or part of it ) to expect after successful login

        """
        # Send SSH command to Garderos
        self.write_channel("ssh " + host + "\n")
        # Wait for username and password prompt
        # Maximum waiting time in seconds is set by variable timeout
        password_sent = False
        login_completed = False
        counter = 0
        output_current = ""
        output_summary = ""
        while not (password_sent and login_completed) and counter < timeout:
            sleep(1)
            output_current = self.read_channel()
            output_summary += output_current
            if "exited" in output_current:
                # SSH session terminated
                # Clear the receive channel before raising exception // Also retrieves error message
                output_current = self.read_channel()
                raise ConnectionError(
                    "Error connecting to host {}. Session terminated unexpectedly. \n{}".format(
                        host, output_current.strip()
                    )
                )
            elif not password_sent and "user" in output_current.lower():
                # Send username when prompted
                self.write_channel(username + "\n")
            elif not password_sent and "password" in output_current.lower():
                # Send password when prompted for the first time
                self.write_channel(password + "\n")
                password_sent = True
            elif password_sent and "password" in output_current.lower():
                # If password has already been sent but a second password prompt appears,
                # this means the password was incorrect
                # Cancel nested SSH connection: CTRL+C followed by ENTER
                self.write_channel(b"\x03".decode("utf-8"))
                sleep(1)
                self.write_channel("\n")
                sleep(2)
                # Clear the receive channel before raising exception
                output_current = self.read_channel()
                raise ValueError(
                    "Authentication error while connecting to host {}.".format(host)
                )
            elif (
                password_sent
                and not login_completed
                and not (expect_prompt in output_current)
            ):
                # After password has been sent, try to send ENTER to device to get the device prompt
                self.write_channel("\n")
            elif (
                password_sent
                and not login_completed
                and expect_prompt in output_current
            ):
                # Device prompt successfully received
                login_completed = True
            # Increase counter in any case
            counter += 1
        # On exit of loop check whether password has been sent
        if not password_sent or not login_completed:
            # Cancel nested SSH connection: CTRL+C followed by ENTER
            self.write_channel(b"\x03".decode("utf-8"))
            sleep(1)
            self.write_channel("\n")
            sleep(2)
            # Clear the receive channel before raising exception
            output_current = self.read_channel()
            raise TimeoutError(
                "Timeout error while connecting to host {}. Transcript of session: \n{}".format(
                    host, output_summary
                )
            )
        return output_current.strip()

    def ssh_send_command(
        self,
        command_string: str,
        expect_string: Optional[str] = None,
        expect_timeout: float = 5.0,
    ) -> str:
        """
        Sending a command through an active nested SSH connection

        :param command_string: Command to be send through nested SSH session

        :param expect_string: Output to be expected from remote device, e.g. command promt

        :param expect_timeout: Timeout in seconds to wait for expect_string in output

        """
        # Send command to channel
        self.write_channel(command_string + "\n")
        output_summary = ""
        # Check if waiting for expect string is necessary
        if expect_string is not None:
            # Read until expect string detected
            output_summary = self.read_until_pattern(
                pattern=expect_string, read_timeout=expect_timeout
            )
        return output_summary
