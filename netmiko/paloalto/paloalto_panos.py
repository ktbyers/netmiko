from typing import Optional, List, Any, Tuple
import re
import warnings
from os import path
from paramiko import SSHClient, Transport

from netmiko.no_enable import NoEnable
from netmiko.base_connection import BaseConnection, DELAY_FACTOR_DEPR_SIMPLE_MSG


class SSHClient_interactive(SSHClient):
    """Set noauth when manually handling SSH authentication."""

    def pa_banner_handler(
        self, title: str, instructions: str, prompt_list: List[Tuple[str, bool]]
    ) -> List[str]:

        resp = []
        for prompt, echo in prompt_list:
            if "Do you accept" in prompt:
                resp.append("yes")
            elif "ssword" in prompt:
                assert isinstance(self.password, str)
                resp.append(self.password)
        return resp

    def _auth(self, username: str, password: str, *args: Any) -> None:
        """
        _auth: args as of aug-2021
        self,
        username,
        password,
        pkey,
        key_filenames,
        allow_agent,
        look_for_keys,
        gss_auth,
        gss_kex,
        gss_deleg_creds,
        gss_host,
        passphrase,
        """

        # Just gets the password up to the pa_banner_handler
        self.password = password
        transport = self.get_transport()
        assert isinstance(transport, Transport)
        transport.auth_interactive(username, handler=self.pa_banner_handler)
        return


class PaloAltoPanosBase(NoEnable, BaseConnection):
    """
    Implement methods for interacting with PaloAlto devices.

    Disables `enable()` and `check_enable_mode()`
    methods.  Overrides several methods for PaloAlto-specific compatibility.
    """

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established.

        Disable paging (the '--more--' prompts).
        Set the base prompt for interaction ('>').
        """
        self.ansi_escape_codes = True
        self._test_channel_read(pattern=r"[>#]")
        self.disable_paging(
            command="set cli scripting-mode on",
            cmd_verify=False,
            pattern=r"[>#].*mode on",
        )
        self.set_terminal_width(
            command="set cli terminal width 500", pattern=r"set cli terminal width 500"
        )
        self.disable_paging(command="set cli pager off")
        self.set_base_prompt()

        # PA devices can be really slow--try to make sure we are caught up
        self.write_channel("show admins\n")
        self._test_channel_read(pattern=r"Client")
        self._test_channel_read(pattern=r"[>#]")

    def find_prompt(
        self, delay_factor: float = 5.0, pattern: Optional[str] = None
    ) -> str:
        """PA devices can be very slow to respond (in certain situations)"""
        return super().find_prompt(delay_factor=delay_factor, pattern=pattern)

    def check_config_mode(
        self, check_string: str = "]", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in configuration mode or not."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def config_mode(
        self, config_command: str = "configure", pattern: str = r"#", re_flags: int = 0
    ) -> str:
        """Enter configuration mode."""
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r">") -> str:
        """Exit configuration mode."""
        return super().exit_config_mode(exit_config=exit_config, pattern=pattern)

    def commit(
        self,
        comment: str = "",
        force: bool = False,
        partial: bool = False,
        device_and_network: bool = False,
        policy_and_objects: bool = False,
        vsys: str = "",
        no_vsys: bool = False,
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
    ) -> str:
        """
        Commit the candidate configuration.

        Commit the entered configuration. Raise an error and return the failure
        if the commit fails.

        Automatically enters configuration mode

        default:
            command_string = commit
        (device_and_network or policy_and_objects or vsys or
                no_vsys) and not partial:
            Exception

        delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        """

        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        if (
            device_and_network or policy_and_objects or vsys or no_vsys
        ) and not partial:
            raise ValueError(
                "'partial' must be True when using "
                "device_and_network or policy_and_objects "
                "or vsys or no_vsys."
            )

        # Select proper command string based on arguments provided
        command_string = "commit"
        commit_marker = "configuration committed successfully"
        if comment:
            command_string += f' description "{comment}"'
        if force:
            command_string += " force"
        if partial:
            command_string += " partial"
            if vsys:
                command_string += f" {vsys}"
            if device_and_network:
                command_string += " device-and-network"
            if policy_and_objects:
                command_string += " device-and-network"
            if no_vsys:
                command_string += " no-vsys"
            command_string += " excluded"

        # Enter config mode (if necessary)
        output = self.config_mode()
        output += self._send_command_str(
            command_string,
            strip_prompt=False,
            strip_command=False,
            expect_string="100%",
            read_timeout=read_timeout,
        )
        output += self.exit_config_mode()

        if commit_marker not in output.lower():
            raise ValueError(f"Commit failed with the following errors:\n\n{output}")
        return output

    def strip_command(self, command_string: str, output: str) -> str:
        """Strip command_string from output string."""
        output_list = output.split(command_string)
        return self.RESPONSE_RETURN.join(output_list)

    def strip_prompt(self, a_string: str) -> str:
        """Strip the trailing router prompt from the output."""
        response_list = a_string.split(self.RESPONSE_RETURN)
        new_response_list = []
        for line in response_list:
            if self.base_prompt not in line:
                new_response_list.append(line)

        output = self.RESPONSE_RETURN.join(new_response_list)
        return self.strip_context_items(output)

    def strip_context_items(self, a_string: str) -> str:
        """Strip PaloAlto-specific output.

        PaloAlto will also put a configuration context:
        [edit]

        This method removes those lines.
        """
        strings_to_strip = [r"\[edit.*\]"]

        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]

        for pattern in strings_to_strip:
            if re.search(pattern, last_line):
                return self.RESPONSE_RETURN.join(response_list[:-1])

        return a_string

    def cleanup(self, command: str = "exit") -> None:
        """Gracefully exit the SSH session."""
        try:
            # The pattern="" forces use of send_command_timing
            if self.check_config_mode(pattern=""):
                self.exit_config_mode()
        except Exception:
            pass
        # Always try to send final 'exit' (command)
        self._session_log_fin = True
        self.write_channel(command + self.RETURN)


class PaloAltoPanosSSH(PaloAltoPanosBase):
    def _build_ssh_client(self) -> SSHClient:
        """Prepare for Paramiko SSH connection."""
        # Create instance of SSHClient object
        # If not using SSH keys, we use noauth

        if not self.use_keys:
            remote_conn_pre: SSHClient = SSHClient_interactive()
        else:
            remote_conn_pre = SSHClient()

        # Load host_keys for better SSH security
        if self.system_host_keys:
            remote_conn_pre.load_system_host_keys()
        if self.alt_host_keys and path.isfile(self.alt_key_file):
            remote_conn_pre.load_host_keys(self.alt_key_file)

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        remote_conn_pre.set_missing_host_key_policy(self.key_policy)
        return remote_conn_pre


class PaloAltoPanosTelnet(PaloAltoPanosBase):
    pass
