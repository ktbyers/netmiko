import re
import time
from typing import (
    Any, 
    Optional,
    Union,
    List,
    Dict,
    Deque
)

from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric.dsa import DSAParameterNumbers

from netmiko import log
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.exceptions import ReadTimeout

from collections import deque
from netmiko.utilities import (
    select_cmd_verify
)
from netmiko.base_connection import (
    flush_session_log,
    structured_data_converter
)

class TPLinkJetStreamBase(CiscoSSHConnection):
    def __init__(self, **kwargs: Any) -> None:
        # TP-Link doesn't have a way to set terminal width which breaks cmd_verify
        if kwargs.get("global_cmd_verify") is None:
            kwargs["global_cmd_verify"] = False
        # TP-Link uses "\r\n" as default_enter for SSH and Telnet
        if kwargs.get("default_enter") is None:
            kwargs["default_enter"] = "\r\n"
        return super().__init__(**kwargs)

    def session_preparation(self) -> None:
        delay_factor = self.select_delay_factor(delay_factor=0)
        time.sleep(0.3 * delay_factor)
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.enable()
        self.set_base_prompt()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def enable(
        self,
        cmd: str = "",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """
        TPLink JetStream requires you to first execute "enable" and then execute "enable-admin".
        This is necessary as "configure" is generally only available at "enable-admin" level

        If the user does not have the Admin role, he will need to execute enable-admin to really
        enable all functions.
        """

        msg = """
Failed to enter enable mode. Please ensure you pass
the 'secret' argument to ConnectHandler.
"""

        # If end-user passes in "cmd" execute that using normal process.
        if cmd:
            return super().enable(
                cmd=cmd,
                pattern=pattern,
                enable_pattern=enable_pattern,
                check_state=check_state,
                re_flags=re_flags,
            )

        output = ""
        if check_state and self.check_enable_mode():
            return output

        for cmd in ("enable", "enable-admin"):
            self.write_channel(self.normalize_cmd(cmd))
            try:
                new_data = self.read_until_prompt_or_pattern(
                    pattern=pattern, re_flags=re_flags, read_entire_line=True
                )
                output += new_data
                if re.search(pattern, new_data):
                    self.write_channel(self.normalize_cmd(self.secret))
                    output += self.read_until_prompt(read_entire_line=True)
            except ReadTimeout:
                raise ValueError(msg)

        if not self.check_enable_mode():
            raise ValueError(msg)
        return output

    def config_mode(
        self, config_command: str = "configure", pattern: str = "", re_flags: int = 0
    ) -> str:
        return super().config_mode(
            config_command=config_command, pattern=pattern, re_flags=re_flags
        )

    def exit_config_mode(self, exit_config: str = "exit", pattern: str = r"#") -> str:
        """
        Exit config mode.

        Like the Mellanox equipment, the TP-Link Jetstream does not
        support a single command to completely exit the configuration mode.

        Consequently, need to keep checking and sending "exit".
        """
        output = ""
        check_count = 12
        while check_count >= 0:
            if self.check_config_mode():
                self.write_channel(self.normalize_cmd(exit_config))
                output += self.read_until_pattern(pattern=pattern)
            else:
                break
            check_count -= 1

        if self.check_config_mode():
            raise ValueError("Failed to exit configuration mode")
            log.debug(f"exit_config_mode: {output}")

        return output

    def check_config_mode(
        self,
        check_string: str = "(config",
        pattern: str = r"#",
        force_regex: bool = False,
    ) -> bool:
        """Check whether device is in configuration mode. Return a boolean."""
        return super().check_config_mode(check_string=check_string, pattern=pattern)

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = ">",
        alt_prompt_terminator: str = "#",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple
        contexts. For TP-Link this will be the router prompt with > or #
        stripped off.

        This will be set on logging in, but not when entering system-view
        """
        return super().set_base_prompt(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            delay_factor=delay_factor,
            pattern=pattern,
        )

    @flush_session_log
    @select_cmd_verify
    def send_command(
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
        raise_parsing_error: bool = False,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """Execute command_string on the SSH channel using a pattern-based mechanism. Generally
        used for show commands. By default this method will keep waiting to receive data until the
        network device prompt is detected. The current network device prompt will be determined
        automatically.

        :param command_string: The command to be executed on the remote device.

        :param expect_string: Regular expression pattern to use for determining end of output.
            If left blank will default to being based on router prompt.

        :param read_timeout: Maximum time to wait looking for pattern. Will raise ReadTimeout
            if timeout is exceeded.

        :param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        :param max_loops: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        :param auto_find_prompt: Use find_prompt() to override base prompt

        :param strip_prompt: Remove the trailing router prompt from the output (default: True).

        :param strip_command: Remove the echo of the command from the output (default: True).

        :param normalize: Ensure the proper enter is sent at end of command (default: True).

        :param use_textfsm: Process command output through TextFSM template (default: False).

        :param textfsm_template: Name of template to parse output with; can be fully qualified
            path, relative path, or name of file in current directory. (default: None).

        :param use_ttp: Process command output through TTP template (default: False).

        :param ttp_template: Name of template to parse output with; can be fully qualified
            path, relative path, or name of file in current directory. (default: None).

        :param use_genie: Process command output through PyATS/Genie parser (default: False).

        :param cmd_verify: Verify command echo before proceeding (default: True).

        :param raise_parsing_error: Raise exception when parsing output to structured data fails.
        """

        # Time to delay in each read loop
        loop_delay = 0.025

        if self.read_timeout_override:
            read_timeout = self.read_timeout_override

        if self.delay_factor_compat:
            # For compatibility calculate the old equivalent read_timeout
            # i.e. what it would have been in Netmiko 3.x
            if delay_factor is None:
                tmp_delay_factor = self.global_delay_factor
            else:
                tmp_delay_factor = self.select_delay_factor(delay_factor)
            compat_timeout = calc_old_timeout(
                max_loops=max_loops,
                delay_factor=tmp_delay_factor,
                loop_delay=0.2,
                old_timeout=self.timeout,
            )
            msg = f"""\n
You have chosen to use Netmiko's delay_factor compatibility mode for
send_command. This will revert Netmiko to behave similarly to how it
did in Netmiko 3.x (i.e. to use delay_factor/global_delay_factor and
max_loops).

Using these parameters Netmiko has calculated an effective read_timeout
of {compat_timeout} and will set the read_timeout to this value.

Please convert your code to that new format i.e.:

    net_connect.send_command(cmd, read_timeout={compat_timeout})

And then disable delay_factor_compat.

delay_factor_compat will be removed in Netmiko 5.x.\n"""
            warnings.warn(msg, DeprecationWarning)

            # Override the read_timeout with Netmiko 3.x way :-(
            read_timeout = compat_timeout

        else:
            # No need for two deprecation messages so only display this if not using
            # delay_factor_compat
            if delay_factor is not None or max_loops is not None:
                msg = """\n
Netmiko 4.x has deprecated the use of delay_factor/max_loops with
send_command. You should convert all uses of delay_factor and max_loops
over to read_timeout=x where x is the total number of seconds to wait
before timing out.\n"""
                warnings.warn(msg, DeprecationWarning)

        if expect_string is not None:
            search_pattern = expect_string
        else:
            search_pattern = self._prompt_handler(auto_find_prompt)

        if normalize:
            command_string = self.normalize_cmd(command_string)

        # Start the clock
        start_time = time.time()
        self.write_channel(command_string)
        new_data = ""

        cmd = command_string.strip()
        if cmd and cmd_verify:
            new_data = self.command_echo_read(cmd=cmd, read_timeout=10)

        MAX_CHARS = 2_000_000
        DEQUE_SIZE = 20
        output = ""
        # Check only the past N-reads. This is for the case where the output is
        # very large (i.e. searching a very large string for a pattern a whole bunch of times)
        past_n_reads: Deque[str] = deque(maxlen=DEQUE_SIZE)
        first_line_processed = False

        # Keep reading data until search_pattern is found or until read_timeout
        while time.time() - start_time < read_timeout:
            if new_data:

                # Because TP-Link doesn't have a way to set terminal width,
                # we need to handle the "Press any key to continue" prompt that appears when the output is too long.
                continue_pattern = r'Press any key to continue \(Q to quit\)'
                if re.search(continue_pattern, new_data):
                    new_data = re.sub(continue_pattern, '', new_data)
                    self.write_channel('a\n')           

                output += new_data
                past_n_reads.append(new_data)

                # Case where we haven't processed the first_line yet (there is a potential issue
                # in the first line (in cases where the line is repainted).
                if not first_line_processed:
                    output, first_line_processed = self._first_line_handler(
                        output, search_pattern
                    )
                    # Check if we have already found our pattern
                    if re.search(search_pattern, output):
                        break

                else:
                    if len(output) <= MAX_CHARS:
                        if re.search(search_pattern, output):
                            break
                    else:
                        # Switch to deque mode if output is greater than MAX_CHARS
                        # Check if pattern is in the past n reads
                        if re.search(search_pattern, "".join(past_n_reads)):
                            break

            time.sleep(loop_delay)
            new_data = self.read_channel()

        else:  # nobreak
            msg = f"""
Pattern not detected: {repr(search_pattern)} in output.

Things you might try to fix this:
1. Explicitly set your pattern using the expect_string argument.
2. Increase the read_timeout to a larger value.

You can also look at the Netmiko session_log or debug log for more information.

"""
            raise ReadTimeout(msg)

        output = self._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )
        return_val = structured_data_converter(
            command=command_string,
            raw_data=output,
            platform=self.device_type,
            use_textfsm=use_textfsm,
            use_ttp=use_ttp,
            use_genie=use_genie,
            textfsm_template=textfsm_template,
            ttp_template=ttp_template,
            raise_parsing_error=raise_parsing_error,
        )
        return return_val

class TPLinkJetStreamSSH(TPLinkJetStreamBase):
    def __init__(self, **kwargs: Any) -> None:
        setattr(dsa, "_check_dsa_parameters", self._override_check_dsa_parameters)
        return super().__init__(**kwargs)

    def _override_check_dsa_parameters(self, parameters: DSAParameterNumbers) -> None:
        """
        Override check_dsa_parameters from cryptography's dsa.py

        Without this the error below occurs:

        ValueError: p must be exactly 1024, 2048, or 3072 bits long

        Allows for shorter or longer parameters.p to be returned
        from the server's host key. This is a HORRIBLE hack and a
        security risk, please remove if possible!

        By now, with firmware:

        2.0.5 Build 20200109 Rel.36203(s)

        It's still not possible to remove this hack.
        """
        if parameters.q.bit_length() not in [160, 256]:
            raise ValueError("q must be exactly 160 or 256 bits long")

        if not (1 < parameters.g < parameters.p):
            raise ValueError("g, p don't satisfy 1 < g < p.")


class TPLinkJetStreamTelnet(TPLinkJetStreamBase):
    def telnet_login(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        username_pattern: str = r"User:",
        pwd_pattern: str = r"Password:",
        delay_factor: float = 1.0,
        max_loops: int = 60,
    ) -> str:
        """Telnet login: can be username/password or just password."""
        return super().telnet_login(
            pri_prompt_terminator=pri_prompt_terminator,
            alt_prompt_terminator=alt_prompt_terminator,
            username_pattern=username_pattern,
            pwd_pattern=pwd_pattern,
            delay_factor=delay_factor,
            max_loops=max_loops,
        )
