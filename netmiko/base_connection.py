"""
Base connection class for netmiko

Handles SSH connection and methods that are generically applicable to different
platforms (Cisco and non-Cisco).

Also defines methods that should generally be supported by child classes
"""

from typing import (
    Optional,
    Callable,
    Any,
    List,
    Dict,
    TypeVar,
    cast,
    Type,
    Sequence,
    Iterator,
    TextIO,
    Union,
    Tuple,
    Deque,
)
from typing import TYPE_CHECKING
from types import TracebackType
import io
import re
import socket
import time
from collections import deque
from os import path
from pathlib import Path
from threading import Lock
import functools
import logging
import itertools

import paramiko
import serial
import warnings

from netmiko import log
from netmiko.netmiko_globals import BACKSPACE_CHAR
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    ConfigInvalidException,
    ReadException,
    ReadTimeout,
)
from netmiko._telnetlib import telnetlib
from netmiko.channel import Channel, SSHChannel, TelnetChannel, SerialChannel
from netmiko.session_log import SessionLog
from netmiko.utilities import (
    write_bytes,
    check_serial_port,
    structured_data_converter,
    run_ttp_template,
    select_cmd_verify,
    calc_old_timeout,
)
from netmiko.utilities import m_exec_time  # noqa
from netmiko import telnet_proxy

if TYPE_CHECKING:
    from os import PathLike

# For decorators
F = TypeVar("F", bound=Callable[..., Any])


DELAY_FACTOR_DEPR_SIMPLE_MSG = """\n
Netmiko 4.x and later has deprecated the use of delay_factor and/or
max_loops in this context. You should remove any use of delay_factor=x
from this method call.\n"""


# Logging filter for #2597
class SecretsFilter(logging.Filter):
    def __init__(self, no_log: Optional[Dict[Any, str]] = None) -> None:
        self.no_log = no_log

    def filter(self, record: logging.LogRecord) -> bool:
        """Removes secrets (no_log) from messages"""
        if self.no_log:
            for hidden_data in self.no_log.values():
                record.msg = record.msg.replace(hidden_data, "********")
        return True


def lock_channel(func: F) -> F:
    @functools.wraps(func)
    def wrapper_decorator(self: "BaseConnection", *args: Any, **kwargs: Any) -> Any:
        self._lock_netmiko_session()
        try:
            return_val = func(self, *args, **kwargs)
        finally:
            # Always unlock the channel, even on exception.
            self._unlock_netmiko_session()
        return return_val

    return cast(F, wrapper_decorator)


def flush_session_log(func: F) -> F:
    @functools.wraps(func)
    def wrapper_decorator(self: "BaseConnection", *args: Any, **kwargs: Any) -> Any:
        try:
            return_val = func(self, *args, **kwargs)
        finally:
            # Always flush the session_log
            if self.session_log:
                self.session_log.flush()
        return return_val

    return cast(F, wrapper_decorator)


def log_writes(func: F) -> F:
    """Handle both session_log and log of writes."""

    @functools.wraps(func)
    def wrapper_decorator(self: "BaseConnection", out_data: str) -> None:
        func(self, out_data)
        try:
            log.debug(
                "write_channel: {}".format(
                    str(write_bytes(out_data, encoding=self.encoding))
                )
            )
            if self.session_log:
                if self.session_log.fin or self.session_log.record_writes:
                    self.session_log.write(out_data)
        except UnicodeDecodeError:
            # Don't log non-ASCII characters; this is null characters and telnet IAC (PY2)
            pass
        return None

    return cast(F, wrapper_decorator)


class BaseConnection:
    """
    Defines vendor independent methods.

    Otherwise method left as a stub method.
    """

    def __init__(
        self,
        ip: str = "",
        host: str = "",
        username: str = "",
        password: Optional[str] = None,
        secret: str = "",
        port: Optional[int] = None,
        device_type: str = "",
        verbose: bool = False,
        global_delay_factor: float = 1.0,
        global_cmd_verify: Optional[bool] = None,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        pkey: Optional[paramiko.PKey] = None,
        passphrase: Optional[str] = None,
        disabled_algorithms: Optional[Dict[str, Any]] = None,
        disable_sha2_fix: bool = False,
        allow_agent: bool = False,
        ssh_strict: bool = False,
        system_host_keys: bool = False,
        alt_host_keys: bool = False,
        alt_key_file: str = "",
        ssh_config_file: Optional[str] = None,
        #
        # Connect timeouts
        # ssh-connect --> TCP conn (conn_timeout) --> SSH-banner (banner_timeout)
        #       --> Auth response (auth_timeout)
        conn_timeout: int = 10,
        # Timeout to wait for authentication response
        auth_timeout: Optional[int] = None,
        banner_timeout: int = 15,  # Timeout to wait for the banner to be presented
        # Other timeouts
        blocking_timeout: int = 20,  # Read blocking timeout
        timeout: int = 100,  # TCP connect timeout | overloaded to read-loop timeout
        session_timeout: int = 60,  # Used for locking/sharing the connection
        read_timeout_override: Optional[float] = None,
        keepalive: int = 0,
        default_enter: Optional[str] = None,
        response_return: Optional[str] = None,
        serial_settings: Optional[Dict[str, Any]] = None,
        fast_cli: bool = True,
        _legacy_mode: bool = False,
        session_log: Optional[SessionLog] = None,
        session_log_record_writes: bool = False,
        session_log_file_mode: str = "write",
        allow_auto_change: bool = False,
        encoding: str = "utf-8",
        sock: Optional[socket.socket] = None,
        sock_telnet: Optional[Dict[str, Any]] = None,
        auto_connect: bool = True,
        delay_factor_compat: bool = False,
        disable_lf_normalization: bool = False,
    ) -> None:
        """
        Initialize attributes for establishing connection to target device.

        :param ip: IP address of target device. Not required if `host` is
            provided.

        :param host: Hostname of target device. Not required if `ip` is
                provided.

        :param username: Username to authenticate against target device if
                required.

        :param password: Password to authenticate against target device if
                required.

        :param secret: The enable password if target device requires one.

        :param port: The destination port used to connect to the target
                device.

        :param device_type: Class selection based on device type.

        :param verbose: Enable additional messages to standard output.

        :param global_delay_factor: Multiplication factor affecting Netmiko delays (default: 1).

        :param use_keys: Connect to target device using SSH keys.

        :param key_file: Filename path of the SSH key file to use.

        :param pkey: SSH key object to use.

        :param passphrase: Passphrase to use for encrypted key; password will be used for key
                decryption if not specified.

        :param disabled_algorithms: Dictionary of SSH algorithms to disable. Refer to the Paramiko
                documentation for a description of the expected format.

        :param disable_sha2_fix: Boolean that fixes Paramiko issue with missing server-sig-algs
            https://github.com/paramiko/paramiko/issues/1961 (default: False)

        :param allow_agent: Enable use of SSH key-agent.

        :param ssh_strict: Automatically reject unknown SSH host keys (default: False, which
                means unknown SSH host keys will be accepted).

        :param system_host_keys: Load host keys from the users known_hosts file.

        :param alt_host_keys: If `True` host keys will be loaded from the file specified in
                alt_key_file.

        :param alt_key_file: SSH host key file to use (if alt_host_keys=True).

        :param ssh_config_file: File name of OpenSSH configuration file.

        :param conn_timeout: TCP connection timeout.

        :param session_timeout: Set a timeout for parallel requests.

        :param auth_timeout: Set a timeout (in seconds) to wait for an authentication response.

        :param banner_timeout: Set a timeout to wait for the SSH banner (pass to Paramiko).

        :param read_timeout_override: Set a timeout that will override the default read_timeout
                of both send_command and send_command_timing. This is useful for 3rd party
                libraries where directly accessing method arguments might be impractical.

        :param keepalive: Send SSH keepalive packets at a specific interval, in seconds.
                Currently defaults to 0, for backwards compatibility (it will not attempt
                to keep the connection alive).

        :param default_enter: Character(s) to send to correspond to enter key (default: \n).

        :param response_return: Character(s) to use in normalized return data to represent
                enter key (default: \n)

        :param serial_settings: Dictionary of settings for use with serial port (pySerial).

        :param fast_cli: Provide a way to optimize for performance. Converts select_delay_factor
                to select smallest of global and specific. Sets default global_delay_factor to .1
                (default: True)

        :param session_log: File path, SessionLog object, or BufferedIOBase subclass object
                to write the session log to.

        :param session_log_record_writes: The session log generally only records channel reads due
                to eliminate command duplication due to command echo. You can enable this if you
                want to record both channel reads and channel writes in the log (default: False).

        :param session_log_file_mode: "write" or "append" for session_log file mode
                (default: "write")

        :param allow_auto_change: Allow automatic configuration changes for terminal settings.
                (default: False)

        :param encoding: Encoding to be used when writing bytes to the output channel.
                (default: "utf-8")

        :param sock: An open socket or socket-like object (such as a `.Channel`) to use for
                communication to the target host (default: None).

        :param sock_telnet: A dictionary of telnet socket parameters (SOCKS proxy). See
                telnet_proxy.py code for details.

        :param global_cmd_verify: Control whether command echo verification is enabled or disabled
                (default: None). Global attribute takes precedence over function `cmd_verify`
                argument. Value of `None` indicates to use function `cmd_verify` argument.

        :param auto_connect: Control whether Netmiko automatically establishes the connection as
                part of the object creation (default: True).

        :param delay_factor_compat: Set send_command and send_command_timing back to using Netmiko
                3.x behavior for delay_factor/global_delay_factor/max_loops. This argument will be
                eliminated in Netmiko 5.x (default: False).

        :param disable_lf_normalization: Disable Netmiko's linefeed normalization behavior
                (default: False)
        """

        self.remote_conn: Union[
            None, telnetlib.Telnet, paramiko.Channel, serial.Serial
        ] = None
        # Does the platform support a configuration mode
        self._config_mode = True
        self._read_buffer = ""
        self.delay_factor_compat = delay_factor_compat

        self.TELNET_RETURN = "\r\n"
        if default_enter is None:
            if "telnet" not in device_type:
                self.RETURN = "\n"
            else:
                self.RETURN = self.TELNET_RETURN
        else:
            self.RETURN = default_enter

        # Line Separator in response lines
        self.RESPONSE_RETURN = "\n" if response_return is None else response_return
        self.disable_lf_normalization = True if disable_lf_normalization else False

        if ip:
            self.host = ip.strip()
        elif host:
            self.host = host.strip()
        if not ip and not host and "serial" not in device_type:
            raise ValueError("Either ip or host must be set")
        if port is None:
            if "telnet" in device_type:
                port = 23
            else:
                port = 22
        self.port = int(port)

        self.username = username
        self.password = password
        self.secret = secret
        self.device_type = device_type
        self.ansi_escape_codes = False
        self.verbose = verbose
        self.auth_timeout = auth_timeout
        self.banner_timeout = banner_timeout
        self.blocking_timeout = blocking_timeout
        self.conn_timeout = conn_timeout
        self.session_timeout = session_timeout
        self.timeout = timeout
        self.read_timeout_override = read_timeout_override
        self.keepalive = keepalive
        self.allow_auto_change = allow_auto_change
        self.encoding = encoding
        self.sock = sock
        self.sock_telnet = sock_telnet
        self.fast_cli = fast_cli
        self._legacy_mode = _legacy_mode
        self.global_delay_factor = global_delay_factor
        self.global_cmd_verify = global_cmd_verify
        if self.fast_cli and self.global_delay_factor == 1:
            self.global_delay_factor = 0.1
        self.session_log = None
        self._session_log_close = False

        # prevent logging secret data
        no_log = {}
        if self.password:
            no_log["password"] = self.password
        if self.secret:
            no_log["secret"] = self.secret
        # Always sanitize username and password
        self._secrets_filter = SecretsFilter(no_log=no_log)
        log.addFilter(self._secrets_filter)

        # Netmiko will close the session_log if we open the file
        if session_log is not None:
            if isinstance(session_log, str):
                # If session_log is a string, open a file corresponding to string name.
                self.session_log = SessionLog(
                    file_name=session_log,
                    file_mode=session_log_file_mode,
                    no_log=no_log,
                    record_writes=session_log_record_writes,
                )
                self.session_log.open()
            elif isinstance(session_log, io.BufferedIOBase):
                # In-memory buffer or an already open file handle
                self.session_log = SessionLog(
                    buffered_io=session_log,
                    no_log=no_log,
                    record_writes=session_log_record_writes,
                )
            elif isinstance(session_log, SessionLog):
                # SessionLog object
                self.session_log = session_log
                self.session_log.open()
            else:
                raise ValueError(
                    "session_log must be a path to a file, a file handle, "
                    "SessionLog object, or a BufferedIOBase subclass."
                )

        # Default values
        self.serial_settings = {
            "port": "COM1",
            "baudrate": 9600,
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
        }
        if serial_settings is None:
            serial_settings = {}
        self.serial_settings.update(serial_settings)

        if "serial" in device_type:
            self.host = "serial"
            comm_port = self.serial_settings.pop("port")
            # Get the proper comm port reference if a name was enterred
            comm_port = check_serial_port(comm_port)
            self.serial_settings.update({"port": comm_port})

        # set in set_base_prompt method
        self.base_prompt = ""
        self._session_locker = Lock()

        # determine if telnet or SSH
        if "_telnet" in device_type:
            self.protocol = "telnet"
            self.password = password or ""
        elif "_serial" in device_type:
            self.protocol = "serial"
            self.password = password or ""
        else:
            self.protocol = "ssh"

            self.key_policy: paramiko.client.MissingHostKeyPolicy
            if not ssh_strict:
                self.key_policy = paramiko.AutoAddPolicy()
            else:
                self.key_policy = paramiko.RejectPolicy()

            # Options for SSH host_keys
            self.use_keys = use_keys
            self.key_file = (
                path.abspath(path.expanduser(key_file)) if key_file else None
            )
            if self.use_keys is True:
                self._key_check()
            self.pkey = pkey
            self.passphrase = passphrase
            self.allow_agent = allow_agent
            self.system_host_keys = system_host_keys
            self.alt_host_keys = alt_host_keys
            self.alt_key_file = alt_key_file
            self.disabled_algorithms = disabled_algorithms

            if disable_sha2_fix:
                sha2_pubkeys = ["rsa-sha2-256", "rsa-sha2-512"]
                if self.disabled_algorithms is None:
                    self.disabled_algorithms = {"pubkeys": sha2_pubkeys}
                else:
                    # Merge sha2_pubkeys into pubkeys and prevent duplicates
                    current_pubkeys = self.disabled_algorithms.get("pubkeys", [])
                    self.disabled_algorithms["pubkeys"] = list(
                        set(current_pubkeys + sha2_pubkeys)
                    )

            # For SSH proxy support
            self.ssh_config_file = ssh_config_file

        # Establish the remote connection
        if auto_connect:
            self._open()

    def _open(self) -> None:
        """Decouple connection creation from __init__ for mocking."""
        self._modify_connection_params()
        self.establish_connection()
        self._try_session_preparation()

    def __enter__(self) -> "BaseConnection":
        """Establish a session using a Context Manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Gracefully close connection on Context Manager exit."""
        self.disconnect()

    def _modify_connection_params(self) -> None:
        """Modify connection parameters prior to SSH connection."""
        pass

    def _timeout_exceeded(self, start: float, msg: str = "Timeout exceeded!") -> bool:
        """Raise NetmikoTimeoutException if waiting too much in the serving queue.

        :param start: Initial start time to see if session lock timeout has been exceeded
        :type start: float (from time.time() call i.e. epoch time)

        :param msg: Exception message if timeout was exceeded
        :type msg: str
        """
        if not start:
            # Must provide a comparison time
            return False
        if time.time() - start > self.session_timeout:
            # session_timeout exceeded
            raise NetmikoTimeoutException(msg)
        return False

    def _lock_netmiko_session(self, start: Optional[float] = None) -> bool:
        """Try to acquire the Netmiko session lock. If not available, wait in the queue until
        the channel is available again.

        :param start: Initial start time to measure the session timeout
        :type start: float (from time.time() call i.e. epoch time)
        """
        if not start:
            start = time.time()
        # Wait here until the SSH channel lock is acquired or until session_timeout exceeded
        while not self._session_locker.acquire(False) and not self._timeout_exceeded(
            start, "The netmiko channel is not available!"
        ):
            time.sleep(0.1)
        return True

    def _unlock_netmiko_session(self) -> None:
        """
        Release the channel at the end of the task.
        """
        if self._session_locker.locked():
            self._session_locker.release()

    def _autodetect_fs(self, cmd: str = "", pattern: str = "") -> str:
        raise NotImplementedError

    def _enter_shell(self) -> str:
        raise NotImplementedError

    def _return_cli(self) -> str:
        raise NotImplementedError

    def _key_check(self) -> bool:
        """Verify key_file exists."""
        msg = f"""
use_keys has been set to True, but specified key_file does not exist:

use_keys: {self.use_keys}
key_file: {self.key_file}
"""
        if self.key_file is None:
            raise ValueError(msg)

        my_key_file = Path(self.key_file)
        if not my_key_file.is_file():
            raise ValueError(msg)
        return True

    @lock_channel
    @log_writes
    def write_channel(self, out_data: str) -> None:
        """Generic method that will write data out the channel.

        :param out_data: data to be written to the channel
        :type out_data: str
        """
        self.channel.write_channel(out_data)

    def is_alive(self) -> bool:
        """Returns a boolean flag with the state of the connection."""
        null = chr(0)
        if self.remote_conn is None:
            log.error("Connection is not initialised, is_alive returns False")
            return False
        if self.protocol == "telnet":
            try:
                # Try sending IAC + NOP (IAC is telnet way of sending command)
                # IAC = Interpret as Command; it comes before the NOP.
                log.debug("Sending IAC + NOP")
                # Need to send multiple times to test connection
                assert isinstance(self.remote_conn, telnetlib.Telnet)
                telnet_socket = self.remote_conn.get_socket()  # type: ignore
                telnet_socket.sendall(telnetlib.IAC + telnetlib.NOP)
                telnet_socket.sendall(telnetlib.IAC + telnetlib.NOP)
                telnet_socket.sendall(telnetlib.IAC + telnetlib.NOP)
                return True
            except AttributeError:
                return False
        else:
            # SSH
            try:
                # Try sending ASCII null byte to maintain the connection alive
                log.debug("Sending the NULL byte")
                self.write_channel(null)
                assert isinstance(self.remote_conn, paramiko.Channel)
                assert self.remote_conn.transport is not None
                result = self.remote_conn.transport.is_active()
                assert isinstance(result, bool)
                return result
            except (socket.error, EOFError):
                log.error("Unable to send", exc_info=True)
                # If unable to send, we can tell for sure that the connection is unusable
                return False
        return False

    @lock_channel
    def read_channel(self) -> str:
        """Generic handler that will read all the data from given channel."""
        new_data = self.channel.read_channel()

        if self.disable_lf_normalization is False:
            start = time.time()
            # Data blocks shouldn't end in '\r' (can cause problems with normalize_linefeeds)
            # Only do the extra read if '\n' exists in the output
            # this avoids devices that only use \r.
            while ("\n" in new_data) and (time.time() - start < 1.0):
                if new_data[-1] == "\r":
                    time.sleep(0.01)
                    new_data += self.channel.read_channel()
                else:
                    break
            new_data = self.normalize_linefeeds(new_data)

        if self.ansi_escape_codes:
            new_data = self.strip_ansi_escape_codes(new_data)
        log.debug(f"read_channel: {new_data}")
        if self.session_log:
            self.session_log.write(new_data)

        # If data had been previously saved to the buffer, the prepend it to output
        # do post read_channel so session_log/log doesn't record buffered data twice
        if self._read_buffer:
            output = self._read_buffer + new_data
            self._read_buffer = ""
        else:
            output = new_data
        return output

    def read_until_pattern(
        self,
        pattern: str = "",
        read_timeout: float = 10.0,
        re_flags: int = 0,
        max_loops: Optional[int] = None,
    ) -> str:
        """Read channel until pattern is detected.

        Will return string up to and including pattern.

        Returns ReadTimeout if pattern not detected in read_timeout seconds.

        :param pattern: Regular expression pattern used to identify that reading is done.

        :param read_timeout: maximum time to wait looking for pattern. Will raise ReadTimeout.
            A read_timeout value of 0 will cause the loop to never timeout (i.e. it will keep
            reading indefinitely until pattern is detected.

        :param re_flags: regex flags used in conjunction with pattern (defaults to no flags).

        :param max_loops: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.
        """
        if max_loops is not None:
            msg = """\n
Netmiko 4.x has deprecated the use of max_loops with read_until_pattern.
You should convert all uses of max_loops over to read_timeout=x
where x is the total number of seconds to wait before timing out.\n"""
            warnings.warn(msg, DeprecationWarning)

        if self.read_timeout_override:
            read_timeout = self.read_timeout_override

        output = ""
        loop_delay = 0.01
        start_time = time.time()
        # if read_timeout == 0 or 0.0 keep reading indefinitely
        while (time.time() - start_time < read_timeout) or (not read_timeout):
            output += self.read_channel()

            if re.search(pattern, output, flags=re_flags):
                if "(" in pattern and "(?:" not in pattern:
                    msg = f"""
Parenthesis found in pattern.

pattern: {pattern}\n

This can be problemtic when used in read_until_pattern().

You should ensure that you use either non-capture groups i.e. '(?:' or that the
parenthesis completely wrap the pattern '(pattern)'"""
                    log.debug(msg)
                results = re.split(pattern, output, maxsplit=1, flags=re_flags)

                # The string matched by pattern must be retained in the output string.
                # re.split will do this if capturing parenthesis are used.
                if len(results) == 2:
                    # no capturing parenthesis, convert and try again.
                    pattern = f"({pattern})"
                    results = re.split(pattern, output, maxsplit=1, flags=re_flags)

                if len(results) != 3:
                    # well, we tried
                    msg = f"""Unable to successfully split output based on pattern:
pattern={pattern}
output={repr(output)}
results={results}
"""
                    raise ReadException(msg)

                # Process such that everything before and including pattern is return.
                # Everything else is retained in the _read_buffer
                output, match_str, buffer = results
                output = output + match_str
                if buffer:
                    self._read_buffer += buffer
                log.debug(f"Pattern found: {pattern} {output}")
                return output
            time.sleep(loop_delay)

        msg = f"""\n\nPattern not detected: {repr(pattern)} in output.

Things you might try to fix this:
1. Adjust the regex pattern to better identify the terminating string. Note, in
many situations the pattern is automatically based on the network device's prompt.
2. Increase the read_timeout to a larger value.

You can also look at the Netmiko session_log or debug log for more information.\n\n"""
        raise ReadTimeout(msg)

    def read_channel_timing(
        self,
        last_read: float = 2.0,
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
    ) -> str:
        """Read data on the channel based on timing delays.

        General pattern is keep reading until no new data is read.

        Once no new data is read wait `last_read` amount of time (one last read).
        As long as no new data, then return data.

        Setting `read_timeout` to zero will cause read_channel_timing to never expire based
        on an absolute timeout. It will only complete based on timeout based on there being
        no new data.

        :param last_read: Amount of time to wait before performing one last read (under the
            idea that we should be done reading at this point and there should be no new
            data).

        :param read_timeout: Absolute timer for how long Netmiko should keep reading data on
            the channel (waiting for there to be no new data). Will raise ReadTimeout if this
            timeout expires. A read_timeout value of 0 will cause the read-loop to never timeout
            (i.e. Netmiko will keep reading indefinitely until there is no new data and last_read
            passes).

        :param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        :param max_loops: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.
        """

        if delay_factor is not None or max_loops is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        if self.read_timeout_override:
            read_timeout = self.read_timeout_override

        # Time to delay in each read loop
        loop_delay = 0.1
        channel_data = ""
        start_time = time.time()

        # Set read_timeout to 0 to never timeout
        while (time.time() - start_time < read_timeout) or (not read_timeout):
            time.sleep(loop_delay)
            new_data = self.read_channel()
            # gather new output
            if new_data:
                channel_data += new_data
            # if we have some output, but nothing new, then do the last read
            elif channel_data != "":
                # Make sure really done (i.e. no new data)
                time.sleep(last_read)
                new_data = self.read_channel()
                if not new_data:
                    break
                else:
                    channel_data += new_data
        else:
            msg = f"""\n
read_channel_timing's absolute timer expired.

The network device was continually outputting data for longer than {read_timeout}
seconds.

If this is expected i.e. the command you are executing is continually emitting
data for a long period of time, then you can set 'read_timeout=x' seconds. If
you want Netmiko to keep reading indefinitely (i.e. to only stop when there is
no new data), then you can set 'read_timeout=0'.

You can look at the Netmiko session_log or debug log for more information.

"""
            raise ReadTimeout(msg)
        return channel_data

    def read_until_prompt(
        self,
        read_timeout: float = 10.0,
        read_entire_line: bool = False,
        re_flags: int = 0,
        max_loops: Optional[int] = None,
    ) -> str:
        """Read channel up to and including self.base_prompt."""
        pattern = re.escape(self.base_prompt)
        if read_entire_line:
            pattern = f"{pattern}.*"
        return self.read_until_pattern(
            pattern=pattern,
            re_flags=re_flags,
            max_loops=max_loops,
            read_timeout=read_timeout,
        )

    def read_until_prompt_or_pattern(
        self,
        pattern: str = "",
        read_timeout: float = 10.0,
        read_entire_line: bool = False,
        re_flags: int = 0,
        max_loops: Optional[int] = None,
    ) -> str:
        """Read until either self.base_prompt or pattern is detected."""
        prompt_pattern = re.escape(self.base_prompt)
        if read_entire_line:
            prompt_pattern = f"{prompt_pattern}.*"
        if pattern:
            combined_pattern = r"(?:{}|{})".format(prompt_pattern, pattern)
        else:
            combined_pattern = prompt_pattern
        return self.read_until_pattern(
            pattern=combined_pattern,
            re_flags=re_flags,
            max_loops=max_loops,
            read_timeout=read_timeout,
        )

    def serial_login(
        self,
        pri_prompt_terminator: str = r"#\s*$",
        alt_prompt_terminator: str = r">\s*$",
        username_pattern: str = r"(?:[Uu]ser:|sername|ogin)",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        return self.telnet_login(
            pri_prompt_terminator,
            alt_prompt_terminator,
            username_pattern,
            pwd_pattern,
            delay_factor,
            max_loops,
        )

    def telnet_login(
        self,
        pri_prompt_terminator: str = r"#\s*$",
        alt_prompt_terminator: str = r">\s*$",
        username_pattern: str = r"(?:user:|username|login|user name)",
        pwd_pattern: str = r"assword",
        delay_factor: float = 1.0,
        max_loops: int = 20,
    ) -> str:
        """Telnet login. Can be username/password or just password.

        :param pri_prompt_terminator: Primary trailing delimiter for identifying a device prompt

        :param alt_prompt_terminator: Alternate trailing delimiter for identifying a device prompt

        :param username_pattern: Pattern used to identify the username prompt

        :param pwd_pattern: Pattern used to identify the pwd prompt

        :param delay_factor: See __init__: global_delay_factor

        :param max_loops: Controls the wait time in conjunction with the delay_factor
        """
        delay_factor = self.select_delay_factor(delay_factor)

        # Revert telnet_login back to old speeds/delays
        if delay_factor < 1:
            if not self._legacy_mode and self.fast_cli:
                delay_factor = 1

        time.sleep(1 * delay_factor)

        output = ""
        return_msg = ""
        i = 1
        while i <= max_loops:
            try:
                output = self.read_channel()
                return_msg += output

                # Search for username pattern / send username
                if re.search(username_pattern, output, flags=re.I):
                    # Sometimes username/password must be terminated with "\r" and not "\r\n"
                    self.write_channel(self.username + "\r")
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for password pattern / send password
                if re.search(pwd_pattern, output, flags=re.I):
                    # Sometimes username/password must be terminated with "\r" and not "\r\n"
                    assert isinstance(self.password, str)
                    self.write_channel(self.password + "\r")
                    time.sleep(0.5 * delay_factor)
                    output = self.read_channel()
                    return_msg += output
                    if re.search(
                        pri_prompt_terminator, output, flags=re.M
                    ) or re.search(alt_prompt_terminator, output, flags=re.M):
                        return return_msg

                # Check if proper data received
                if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
                    alt_prompt_terminator, output, flags=re.M
                ):
                    return return_msg

                self.write_channel(self.TELNET_RETURN)
                time.sleep(0.5 * delay_factor)
                i += 1
            except EOFError:
                assert self.remote_conn is not None
                self.remote_conn.close()
                msg = f"Login failed: {self.host}"
                raise NetmikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(0.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return return_msg

        msg = f"Login failed: {self.host}"
        assert self.remote_conn is not None
        self.remote_conn.close()
        raise NetmikoAuthenticationException(msg)

    def _try_session_preparation(self, force_data: bool = True) -> None:
        """
        In case of an exception happening during `session_preparation()` Netmiko should
        gracefully clean-up after itself. This might be challenging for library users
        to do since they do not have a reference to the object. This is possibly related
        to threads used in Paramiko.
        """
        try:
            # Netmiko needs there to be data for session_preparation to work.
            if force_data:
                self.write_channel(self.RETURN)
                time.sleep(0.1)
            self.session_preparation()
        except Exception:
            self.disconnect()
            raise

    def session_preparation(self) -> None:
        """
        Prepare the session after the connection has been established

        This method handles some differences that occur between various devices
        early on in the session.

        In general, it should include:
        self._test_channel_read(pattern=r"some_pattern")
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()
        """
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

    def _use_ssh_config(self, dict_arg: Dict[str, Any]) -> Dict[str, Any]:
        """Update SSH connection parameters based on contents of SSH config file.

        :param dict_arg: Dictionary of SSH connection parameters
        """
        connect_dict = dict_arg.copy()

        # Use SSHConfig to generate source content.
        assert self.ssh_config_file is not None
        full_path = path.abspath(path.expanduser(self.ssh_config_file))
        source: Union[paramiko.config.SSHConfigDict, Dict[str, Any]]
        if path.exists(full_path):
            ssh_config_instance = paramiko.SSHConfig()
            with io.open(full_path, "rt", encoding="utf-8") as f:
                ssh_config_instance.parse(f)
                source = ssh_config_instance.lookup(self.host)
        else:
            source = {}

        # Keys get normalized to lower-case
        proxy: Optional[paramiko.proxy.ProxyCommand]
        if "proxycommand" in source:
            proxy = paramiko.ProxyCommand(source["proxycommand"])
        elif "proxyjump" in source:
            hops = list(reversed(source["proxyjump"].split(",")))
            if len(hops) > 1:
                raise ValueError(
                    "ProxyJump with more than one proxy server is not supported."
                )
            port = source.get("port", self.port)
            host = source.get("hostname", self.host)
            # -F {full_path} forces the continued use of the same SSH config file
            cmd = "ssh -F {} -W {}:{} {}".format(full_path, host, port, hops[0])
            proxy = paramiko.ProxyCommand(cmd)
        else:
            proxy = None

        # Only update 'hostname', 'sock', 'port', and 'username'
        # For 'port' and 'username' only update if using object defaults
        if connect_dict["port"] == 22:
            connect_dict["port"] = int(source.get("port", self.port))
        if connect_dict["username"] == "":
            connect_dict["username"] = source.get("user", self.username)
        if proxy:
            connect_dict["sock"] = proxy
        connect_dict["hostname"] = source.get("hostname", self.host)

        return connect_dict

    def _connect_params_dict(self) -> Dict[str, Any]:
        """Generate dictionary of Paramiko connection parameters."""
        conn_dict = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "look_for_keys": self.use_keys,
            "allow_agent": self.allow_agent,
            "key_filename": self.key_file,
            "pkey": self.pkey,
            "passphrase": self.passphrase,
            "disabled_algorithms": self.disabled_algorithms,
            "timeout": self.conn_timeout,
            "auth_timeout": self.auth_timeout,
            "banner_timeout": self.banner_timeout,
            "sock": self.sock,
        }

        # Check if using SSH 'config' file mainly for SSH proxy support
        if self.ssh_config_file:
            conn_dict = self._use_ssh_config(conn_dict)
        return conn_dict

    def _sanitize_output(
        self,
        output: str,
        strip_command: bool = False,
        command_string: Optional[str] = None,
        strip_prompt: bool = False,
    ) -> str:
        """Strip out command echo and trailing router prompt."""
        if strip_command and command_string:
            output = self.strip_command(command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)
        return output

    def establish_connection(self, width: int = 511, height: int = 1000) -> None:
        """Establish SSH connection to the network device

        Timeout will generate a NetmikoTimeoutException
        Authentication failure will generate a NetmikoAuthenticationException

        :param width: Specified width of the VT100 terminal window (default: 511)
        :type width: int

        :param height: Specified height of the VT100 terminal window (default: 1000)
        :type height: int
        """
        self.channel: Channel
        if self.protocol == "telnet":
            if self.sock_telnet:
                self.remote_conn = telnet_proxy.Telnet(
                    self.host,
                    port=self.port,
                    timeout=self.timeout,
                    proxy_dict=self.sock_telnet,
                )
            else:
                self.remote_conn = telnetlib.Telnet(  # type: ignore
                    self.host, port=self.port, timeout=self.timeout
                )
            # Migrating communication to channel class
            self.channel = TelnetChannel(conn=self.remote_conn, encoding=self.encoding)
            self.telnet_login()
        elif self.protocol == "serial":
            self.remote_conn = serial.Serial(**self.serial_settings)
            self.channel = SerialChannel(conn=self.remote_conn, encoding=self.encoding)
            self.serial_login()
        elif self.protocol == "ssh":
            ssh_connect_params = self._connect_params_dict()
            self.remote_conn_pre: Optional[paramiko.SSHClient]
            self.remote_conn_pre = self._build_ssh_client()

            # initiate SSH connection
            try:
                self.remote_conn_pre.connect(**ssh_connect_params)
            except socket.error as conn_error:
                self.paramiko_cleanup()
                msg = f"""TCP connection to device failed.

Common causes of this problem are:
1. Incorrect hostname or IP address.
2. Wrong TCP port.
3. Intermediate firewall blocking access.

Device settings: {self.device_type} {self.host}:{self.port}

"""

                # Handle DNS failures separately
                if "Name or service not known" in str(conn_error):
                    msg = (
                        f"DNS failure--the hostname you provided was not resolvable "
                        f"in DNS: {self.host}:{self.port}"
                    )

                msg = msg.lstrip()
                raise NetmikoTimeoutException(msg)
            except paramiko.ssh_exception.AuthenticationException as auth_err:
                self.paramiko_cleanup()
                msg = f"""Authentication to device failed.

Common causes of this problem are:
1. Invalid username and password
2. Incorrect SSH-key file
3. Connecting to the wrong device

Device settings: {self.device_type} {self.host}:{self.port}

"""

                msg += self.RETURN + str(auth_err)
                raise NetmikoAuthenticationException(msg)
            except paramiko.ssh_exception.SSHException as e:
                self.paramiko_cleanup()
                if "No existing session" in str(e):
                    msg = (
                        "Paramiko: 'No existing session' error: "
                        "try increasing 'conn_timeout' to 15 seconds or larger."
                    )
                    raise NetmikoTimeoutException(msg)
                else:
                    msg = f"""
A paramiko SSHException occurred during connection creation:

{str(e)}

"""
                    raise NetmikoTimeoutException(msg)

            if self.verbose:
                print(f"SSH connection established to {self.host}:{self.port}")

            # Use invoke_shell to establish an 'interactive session'
            self.remote_conn = self.remote_conn_pre.invoke_shell(
                term="vt100", width=width, height=height
            )

            self.remote_conn.settimeout(self.blocking_timeout)
            if self.keepalive:
                assert isinstance(self.remote_conn.transport, paramiko.Transport)
                self.remote_conn.transport.set_keepalive(self.keepalive)

            # Migrating communication to channel class
            self.channel = SSHChannel(conn=self.remote_conn, encoding=self.encoding)

            self.special_login_handler()
            if self.verbose:
                print("Interactive SSH session established")

        return None

    def _test_channel_read(self, count: int = 40, pattern: str = "") -> str:
        """Try to read the channel (generally post login) verify you receive data back.

        :param count: the number of times to check the channel for data

        :param pattern: Regular expression pattern used to determine end of channel read
        """

        def _increment_delay(
            main_delay: float, increment: float = 1.1, maximum: int = 8
        ) -> float:
            """Increment sleep time to a maximum value."""
            main_delay = main_delay * increment
            if main_delay >= maximum:
                main_delay = maximum
            return main_delay

        i = 0
        delay_factor = self.select_delay_factor(delay_factor=0)

        if pattern:
            return self.read_until_pattern(pattern=pattern, read_timeout=20)

        main_delay = delay_factor * 0.1
        time.sleep(main_delay * 10)
        new_data = ""
        while i <= count:
            new_data += self.read_channel_timing(read_timeout=20)
            if new_data:
                return new_data

            self.write_channel(self.RETURN)
            main_delay = _increment_delay(main_delay)
            time.sleep(main_delay)
            i += 1

        raise NetmikoTimeoutException("Timed out waiting for data")

    def _build_ssh_client(self) -> paramiko.SSHClient:
        """Prepare for Paramiko SSH connection."""
        # Create instance of SSHClient object
        remote_conn_pre = paramiko.SSHClient()

        # Load host_keys for better SSH security
        if self.system_host_keys:
            remote_conn_pre.load_system_host_keys()
        if self.alt_host_keys and path.isfile(self.alt_key_file):
            remote_conn_pre.load_host_keys(self.alt_key_file)

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        remote_conn_pre.set_missing_host_key_policy(self.key_policy)
        return remote_conn_pre

    def select_delay_factor(self, delay_factor: float) -> float:
        """
        Choose the greater of delay_factor or self.global_delay_factor (default).
        In fast_cli choose the lesser of delay_factor of self.global_delay_factor.

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        if self.fast_cli:
            if delay_factor and delay_factor <= self.global_delay_factor:
                return delay_factor
            else:
                return self.global_delay_factor
        else:
            if delay_factor >= self.global_delay_factor:
                return delay_factor
            else:
                return self.global_delay_factor

    def special_login_handler(self, delay_factor: float = 1.0) -> None:
        """Handler for devices like WLC, Extreme ERS that throw up characters prior to login."""
        pass

    def disable_paging(
        self,
        command: str = "terminal length 0",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        """Disable paging default to a Cisco CLI method.

        :param command: Device command to disable pagination of output

        :param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        :param cmd_verify: Verify command echo before proceeding (default: True).

        :param pattern: Pattern to terminate reading of channel
        """
        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        command = self.normalize_cmd(command)
        log.debug("In disable_paging")
        log.debug(f"Command: {command}")
        self.write_channel(command)
        # Make sure you read until you detect the command echo (avoid getting out of sync)
        if cmd_verify and self.global_cmd_verify is not False:
            output = self.read_until_pattern(
                pattern=re.escape(command.strip()), read_timeout=20
            )
        elif pattern:
            output = self.read_until_pattern(pattern=pattern, read_timeout=20)
        else:
            output = self.read_until_prompt()
        log.debug(f"{output}")
        log.debug("Exiting disable_paging")
        return output

    def set_terminal_width(
        self,
        command: str = "",
        delay_factor: Optional[float] = None,
        cmd_verify: bool = False,
        pattern: Optional[str] = None,
    ) -> str:
        """CLI terminals try to automatically adjust the line based on the width of the terminal.
        This causes the output to get distorted when accessed programmatically.

        Set terminal width to 511 which works on a broad set of devices.

        :param command: Command string to send to the device

        :param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.
        """
        if delay_factor is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        if not command:
            return ""
        command = self.normalize_cmd(command)
        self.write_channel(command)

        # Avoid cmd_verify here as terminal width must be set before doing cmd_verify
        if cmd_verify and self.global_cmd_verify is not False:
            output = self.read_until_pattern(pattern=re.escape(command.strip()))
        elif pattern:
            output = self.read_until_pattern(pattern=pattern)
        else:
            output = self.read_until_prompt()
        return output

    def set_base_prompt(
        self,
        pri_prompt_terminator: str = "#",
        alt_prompt_terminator: str = ">",
        delay_factor: float = 1.0,
        pattern: Optional[str] = None,
    ) -> str:
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
        if pattern is None:
            if pri_prompt_terminator and alt_prompt_terminator:
                pri_term = re.escape(pri_prompt_terminator)
                alt_term = re.escape(alt_prompt_terminator)
                pattern = rf"({pri_term}|{alt_term})"
            elif pri_prompt_terminator:
                pattern = re.escape(pri_prompt_terminator)
            elif alt_prompt_terminator:
                pattern = re.escape(alt_prompt_terminator)

        if pattern:
            prompt = self.find_prompt(delay_factor=delay_factor, pattern=pattern)
        else:
            prompt = self.find_prompt(delay_factor=delay_factor)

        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError(f"Router prompt not found: {repr(prompt)}")

        # If all we have is the 'terminator' just use that :-(
        if len(prompt) == 1:
            self.base_prompt = prompt
        else:
            # Strip off trailing terminator
            self.base_prompt = prompt[:-1]
        return self.base_prompt

    def find_prompt(
        self, delay_factor: float = 1.0, pattern: Optional[str] = None
    ) -> str:
        """Finds the current network device prompt, last line only.

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int

        :param pattern: Regular expression pattern to determine whether prompt is valid
        """
        delay_factor = self.select_delay_factor(delay_factor)
        sleep_time = delay_factor * 0.25
        self.clear_buffer()
        self.write_channel(self.RETURN)

        if pattern:
            prompt = self.read_until_pattern(pattern=pattern)
        else:
            # Initial read
            time.sleep(sleep_time)
            prompt = self.read_channel().strip()

            count = 0
            while count <= 12 and not prompt:
                if not prompt:
                    self.write_channel(self.RETURN)
                    time.sleep(sleep_time)
                    prompt = self.read_channel().strip()
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
        if not prompt:
            raise ValueError(f"Unable to find prompt: {prompt}")
        log.debug(f"[find_prompt()]: prompt is {prompt}")
        return prompt

    def clear_buffer(
        self,
        backoff: bool = True,
        backoff_max: float = 3.0,
        delay_factor: Optional[float] = None,
    ) -> str:
        """Read any data available in the channel."""

        if delay_factor is None:
            delay_factor = self.global_delay_factor
        sleep_time = 0.1 * delay_factor

        output = ""
        for _ in range(10):
            time.sleep(sleep_time)
            data = self.read_channel()
            data = self.strip_ansi_escape_codes(data)
            output += data
            if not data:
                break
            # Double sleep time each time we detect data
            log.debug("Clear buffer detects data in the channel")
            if backoff:
                sleep_time *= 2
                sleep_time = backoff_max if sleep_time >= backoff_max else sleep_time
        return output

    def command_echo_read(self, cmd: str, read_timeout: float) -> str:
        # Make sure you read until you detect the command echo (avoid getting out of sync)
        new_data = self.read_until_pattern(
            pattern=re.escape(cmd), read_timeout=read_timeout
        )

        # There can be echoed prompts that haven't been cleared before the cmd echo
        # this can later mess up the trailing prompt pattern detection. Clear this out.
        lines = new_data.split(cmd)
        if len(lines) == 2:
            # lines[-1] should realistically just be the null string
            new_data = f"{cmd}{lines[-1]}"
        else:
            # cmd exists in the output multiple times? Just retain the original output
            pass
        return new_data

    @flush_session_log
    @select_cmd_verify
    def send_command_timing(
        self,
        command_string: str,
        last_read: float = 2.0,
        read_timeout: float = 120.0,
        delay_factor: Optional[float] = None,
        max_loops: Optional[int] = None,
        strip_prompt: bool = True,
        strip_command: bool = True,
        normalize: bool = True,
        use_textfsm: bool = False,
        textfsm_template: Optional[str] = None,
        use_ttp: bool = False,
        ttp_template: Optional[str] = None,
        use_genie: bool = False,
        cmd_verify: bool = False,
        raise_parsing_error: bool = False,
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """Execute command_string on the SSH channel using a delay-based mechanism. Generally
        used for show commands.

        :param command_string: The command to be executed on the remote device.

        :param last_read: Time waited after end of data

        :param read_timeout: Absolute timer for how long Netmiko should keep reading data on
            the channel (waiting for there to be no new data). Will raise ReadTimeout if this
            timeout expires. A read_timeout value of 0 will cause the read-loop to never timeout
            (i.e. Netmiko will keep reading indefinitely until there is no new data and last_read
            passes).

        :param delay_factor: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

        :param max_loops: Deprecated in Netmiko 4.x. Will be eliminated in Netmiko 5.

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

        :param cmd_verify: Verify command echo before proceeding (default: False).

        :param raise_parsing_error: Raise exception when parsing output to structured data fails.
        """
        if delay_factor is not None or max_loops is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

        output = ""
        new_data = ""
        if normalize:
            command_string = self.normalize_cmd(command_string)
        self.write_channel(command_string)

        cmd = command_string.strip()
        if cmd and cmd_verify:
            new_data = self.command_echo_read(cmd=cmd, read_timeout=10)
        output += new_data
        output += self.read_channel_timing(
            last_read=last_read, read_timeout=read_timeout
        )

        output = self._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )
        return_data = structured_data_converter(
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
        return return_data

    def _send_command_timing_str(self, *args: Any, **kwargs: Any) -> str:
        """Wrapper for `send_command_timing` method that always returns a
        string"""
        output = self.send_command_timing(*args, **kwargs)
        assert isinstance(output, str)
        return output

    def strip_prompt(self, a_string: str) -> str:
        """Strip the trailing router prompt from the output.

        :param a_string: Returned string from device
        :type a_string: str
        """
        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]

        if self.base_prompt in last_line:
            return self.RESPONSE_RETURN.join(response_list[:-1])
        else:
            return a_string

    def _first_line_handler(self, data: str, search_pattern: str) -> Tuple[str, bool]:
        """
        In certain situations the first line will get repainted which causes a false
        match on the terminating pattern.

        Filter this out.

        returns a tuple of (data, first_line_processed)

        Where data is the original data potentially with the first line modified
        and the first_line_processed is a flag indicating that we have handled the
        first line.
        """
        try:
            # First line is the echo line containing the command. In certain situations
            # it gets repainted and needs filtered
            lines = data.split(self.RETURN)
            first_line = lines[0]
            if BACKSPACE_CHAR in first_line:
                pattern = search_pattern + r".*$"
                first_line = re.sub(pattern, repl="", string=first_line)
                lines[0] = first_line
                data = self.RETURN.join(lines)
            return (data, True)
        except IndexError:
            return (data, False)

    def _prompt_handler(self, auto_find_prompt: bool) -> str:
        if auto_find_prompt:
            try:
                prompt = self.find_prompt()
            except ValueError:
                prompt = self.base_prompt
        else:
            prompt = self.base_prompt
        return re.escape(prompt.strip())

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

    def _send_command_str(self, *args: Any, **kwargs: Any) -> str:
        """Wrapper for `send_command` method that always returns a string"""
        output = self.send_command(*args, **kwargs)
        assert isinstance(output, str)
        return output

    def send_command_expect(
        self, *args: Any, **kwargs: Any
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """Support previous name of send_command method."""
        return self.send_command(*args, **kwargs)

    def _multiline_kwargs(self, **kwargs: Any) -> Dict[str, Any]:
        strip_prompt = kwargs.get("strip_prompt", False)
        kwargs["strip_prompt"] = strip_prompt
        strip_command = kwargs.get("strip_command", False)
        kwargs["strip_command"] = strip_command
        return kwargs

    def send_multiline(
        self,
        commands: Sequence[Union[str, List[str]]],
        multiline: bool = True,
        **kwargs: Any,
    ) -> str:
        """
        commands should either be:

        commands = [[cmd1, expect1], [cmd2, expect2], ...]]

        Or

        commands = [cmd1, cmd2, cmd3, ...]

        Any expect_string that is a null-string will use pattern based on
        device's prompt (unless expect_string argument is passed in via
        kwargs.

        """
        output = ""
        if multiline:
            kwargs = self._multiline_kwargs(**kwargs)

        default_expect_string = kwargs.pop("expect_string", None)
        if not default_expect_string:
            auto_find_prompt = kwargs.get("auto_find_prompt", True)
            default_expect_string = self._prompt_handler(auto_find_prompt)

        if commands and isinstance(commands[0], str):
            # If list of commands just send directly using default_expect_string (probably prompt)
            for cmd in commands:
                cmd = str(cmd)
                output += self._send_command_str(
                    cmd, expect_string=default_expect_string, **kwargs
                )
        else:
            # If list of lists, then first element is cmd and second element is expect_string
            for cmd_item in commands:
                assert not isinstance(cmd_item, str)
                cmd, expect_string = cmd_item
                if not expect_string:
                    expect_string = default_expect_string
                output += self._send_command_str(
                    cmd, expect_string=expect_string, **kwargs
                )
        return output

    def send_multiline_timing(
        self, commands: Sequence[str], multiline: bool = True, **kwargs: Any
    ) -> str:
        if multiline:
            kwargs = self._multiline_kwargs(**kwargs)
        output = ""
        for cmd in commands:
            cmd = str(cmd)
            output += self._send_command_timing_str(cmd, **kwargs)
        return output

    @staticmethod
    def strip_backspaces(output: str) -> str:
        """Strip any backspace characters out of the output.

        :param output: Output obtained from a remote network device.
        :type output: str
        """
        backspace_char = "\x08"
        return output.replace(backspace_char, "")

    def strip_command(self, command_string: str, output: str) -> str:
        """
        Strip command_string from output string

        Cisco IOS adds backspaces into output for long commands (i.e. for commands that line wrap)

        :param command_string: The command string sent to the device
        :type command_string: str

        :param output: The returned output as a result of the command string sent to the device
        :type output: str
        """
        backspace_char = "\x08"

        # Check for line wrap (remove backspaces)
        if backspace_char in output:
            output = output.replace(backspace_char, "")

        # Juniper has a weird case where the echoed command will be " \n"
        # i.e. there is an extra space there.
        cmd = command_string.strip()
        if output.startswith(cmd):
            output_lines = output.split(self.RESPONSE_RETURN)
            new_output = output_lines[1:]
            return self.RESPONSE_RETURN.join(new_output)
        else:
            # command_string isn't there; do nothing
            return output

    def normalize_linefeeds(self, a_string: str) -> str:
        """Convert `\r\r\n`,`\r\n`, `\n\r` to `\n.`

        :param a_string: A string that may have non-normalized line feeds
            i.e. output returned from device, or a device prompt
        :type a_string: str
        """
        newline = re.compile("(\r\r\r\n|\r\r\n|\r\n|\n\r)")
        a_string = newline.sub(self.RESPONSE_RETURN, a_string)
        if self.RESPONSE_RETURN == "\n":
            # Convert any remaining \r to \n
            return re.sub("\r", self.RESPONSE_RETURN, a_string)
        else:
            return a_string

    def normalize_cmd(self, command: str) -> str:
        """Normalize CLI commands to have a single trailing newline.

        :param command: Command that may require line feed to be normalized
        :type command: str
        """
        command = command.rstrip()
        command += self.RETURN
        return command

    def check_enable_mode(self, check_string: str = "") -> bool:
        """Check if in enable mode. Return boolean.

        :param check_string: Identification of privilege mode from device
        :type check_string: str
        """
        self.write_channel(self.RETURN)
        output = self.read_until_prompt(read_entire_line=True)
        return check_string in output

    def enable(
        self,
        cmd: str = "",
        pattern: str = "ssword",
        enable_pattern: Optional[str] = None,
        check_state: bool = True,
        re_flags: int = re.IGNORECASE,
    ) -> str:
        """Enter enable mode.

        :param cmd: Device command to enter enable mode

        :param pattern: pattern to search for indicating device is waiting for password

        :param enable_pattern: pattern indicating you have entered enable mode

        :param check_state: Determine whether we are already in enable_mode using
                check_enable_mode() before trying to elevate privileges (default: True)

        :param re_flags: Regular expression flags used in conjunction with pattern
        """
        output = ""
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )

        # Check if in enable mode already.
        if check_state and self.check_enable_mode():
            return output

        # Send "enable" mode command
        self.write_channel(self.normalize_cmd(cmd))
        try:
            # Read the command echo
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(pattern=re.escape(cmd.strip()))

            # Search for trailing prompt or password pattern
            output += self.read_until_prompt_or_pattern(
                pattern=pattern, re_flags=re_flags
            )

            # Send the "secret" in response to password pattern
            if re.search(pattern, output):
                self.write_channel(self.normalize_cmd(self.secret))
                output += self.read_until_prompt()

            # Search for terminating pattern if defined
            if enable_pattern and not re.search(enable_pattern, output):
                output += self.read_until_pattern(pattern=enable_pattern)
            else:
                if not self.check_enable_mode():
                    raise ValueError(msg)

        except NetmikoTimeoutException:
            raise ValueError(msg)

        return output

    def exit_enable_mode(self, exit_command: str = "") -> str:
        """Exit enable mode.

        :param exit_command: Command that exits the session from privileged mode
        :type exit_command: str
        """
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            output += self.read_until_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def check_config_mode(
        self, check_string: str = "", pattern: str = "", force_regex: bool = False
    ) -> bool:
        """Checks if the device is in configuration mode or not.

        :param check_string: Identification of configuration mode from the device
        :type check_string: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str

        :param force_regex: Use regular expression pattern to find check_string in output
        :type force_regex: bool

        """
        self.write_channel(self.RETURN)
        # You can encounter an issue here (on router name changes) prefer delay-based solution
        if not pattern:
            output = self.read_channel_timing(read_timeout=10.0)
        else:
            output = self.read_until_pattern(pattern=pattern)

        if force_regex:
            return bool(re.search(check_string, output))
        else:
            return check_string in output

    def config_mode(
        self, config_command: str = "", pattern: str = "", re_flags: int = 0
    ) -> str:
        """Enter into config_mode.

        :param config_command: Configuration command to send to the device
        :type config_command: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str

        :param re_flags: Regular expression flags
        :type re_flags: RegexFlag
        """
        output = ""
        if not self.check_config_mode():
            self.write_channel(self.normalize_cmd(config_command))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(config_command.strip())
                )
            if pattern:
                output += self.read_until_pattern(pattern=pattern, re_flags=re_flags)
            else:
                output += self.read_until_prompt(read_entire_line=True)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode.")
        return output

    def exit_config_mode(self, exit_config: str = "", pattern: str = "") -> str:
        """Exit from configuration mode.

        :param exit_config: Command to exit configuration mode
        :type exit_config: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str
        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(exit_config.strip())
                )
            if pattern:
                output += self.read_until_pattern(pattern=pattern)
            else:
                output += self.read_until_prompt(read_entire_line=True)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        log.debug(f"exit_config_mode: {output}")
        return output

    def send_config_from_file(
        self, config_file: Union[str, bytes, "PathLike[Any]"], **kwargs: Any
    ) -> str:
        """
        Send configuration commands down the SSH channel from a file.

        The file is processed line-by-line and each command is sent down the
        SSH channel.

        **kwargs are passed to send_config_set method.

        :param config_file: Path to configuration file to be sent to the device

        :param kwargs: params to be sent to send_config_set method
        """
        with io.open(config_file, "rt", encoding="utf-8") as cfg_file:
            commands = cfg_file.readlines()
        return self.send_config_set(commands, **kwargs)

    @flush_session_log
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

        if self.global_cmd_verify is not None:
            cmd_verify = self.global_cmd_verify

        if delay_factor is not None or max_loops is not None:
            warnings.warn(DELAY_FACTOR_DEPR_SIMPLE_MSG, DeprecationWarning)

            # Calculate an equivalent read_timeout (if using old settings)
            # Eliminate in Netmiko 5.x
            if read_timeout is None:
                max_loops = 150 if max_loops is None else max_loops
                delay_factor = 1.0 if delay_factor is None else delay_factor

                # If delay_factor has been set, then look at global_delay_factor
                delay_factor = self.select_delay_factor(delay_factor)

                read_timeout = calc_old_timeout(
                    max_loops=max_loops, delay_factor=delay_factor, loop_delay=0.1
                )

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
            # Make a copy of the iterator
            config_commands, config_commands_tmp = itertools.tee(config_commands, 2)
            bypass_detected = any(
                [True for cmd in config_commands_tmp if re.search(bypass_commands, cmd)]
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

            # Standard output gathering (no error_pattern)
            if not error_pattern:
                output += self.read_channel_timing(read_timeout=read_timeout)

        else:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))

                # Make sure command is echoed
                output += self.read_until_pattern(
                    pattern=re.escape(cmd.strip()), read_timeout=read_timeout
                )

                # Read until next prompt or terminator (#); the .*$ forces read of entire line
                pattern = f"(?:{re.escape(self.base_prompt)}.*$|{terminator}.*$)"
                output += self.read_until_pattern(
                    pattern=pattern, read_timeout=read_timeout, re_flags=re.M
                )

                if error_pattern:
                    if re.search(error_pattern, output, flags=re.M):
                        msg = f"Invalid input detected at command: {cmd}"
                        raise ConfigInvalidException(msg)

        if exit_config_mode:
            output += self.exit_config_mode()
        output = self._sanitize_output(output)
        log.debug(f"{output}")
        return output

    def strip_ansi_escape_codes(self, string_buffer: str) -> str:
        """
        Remove any ANSI (VT100) ESC codes from the output

        http://en.wikipedia.org/wiki/ANSI_escape_code

        Note: this does not capture ALL possible ANSI Escape Codes only the ones
        that have been encountered

        Current codes that are filtered:
        ESC = '\x1b' or chr(27)
        ESC = is the escape character [^ in hex ('\x1b')
        ESC[24;27H   Position cursor
        ESC[?25h     Show the cursor
        ESC[E        Next line (HP does ESC-E)
        ESC[K        Erase line from cursor to the end of line
        ESC[2K       Erase entire line
        ESC[1;24r    Enable scrolling from start to row end
        ESC[?6l      Reset mode screen with options 640 x 200 monochrome (graphics)
        ESC[?7l      Disable line wrapping
        ESC[2J       Code erase display
        ESC[00;32m   Color Green (30 to 37 are different colors)
        ESC[6n       Get cursor position
        ESC[1D       Move cursor position leftward by x characters (1 in this case)
        ESC[9999B    Move cursor down N-lines (very large value is attempt to move to the
                     very bottom of the screen)
        ESC[c        Query Device (used by MikroTik in 'Safe-Mode')
        ESC[2004h    Enable bracketed paste mode
        ESC[2004l    Disable bracketed paste mode

        :param string_buffer: The string to be processed to remove ANSI escape codes
        :type string_buffer: str
        """  # noqa

        code_position_cursor = chr(27) + r"\[\d+;\d+H"
        code_show_cursor = chr(27) + r"\[\?25h"
        code_next_line = chr(27) + r"E"
        code_erase_line_end = chr(27) + r"\[K"
        code_erase_line = chr(27) + r"\[2K"
        code_erase_start_line = chr(27) + r"\[K"
        code_enable_scroll = chr(27) + r"\[\d+;\d+r"
        code_insert_line = chr(27) + r"\[(\d+)L"
        code_carriage_return = chr(27) + r"\[1M"
        code_disable_line_wrapping = chr(27) + r"\[\?7l"
        code_reset_mode_screen_options = chr(27) + r"\[\?\d+l"
        code_reset_graphics_mode = chr(27) + r"\[00m"
        code_erase_display = chr(27) + r"\[2J"
        code_erase_display_0 = chr(27) + r"\[J"
        code_graphics_mode = chr(27) + r"\[\dm"
        code_graphics_mode1 = chr(27) + r"\[\d\d;\d\dm"
        code_graphics_mode2 = chr(27) + r"\[\d\d;\d\d;\d\dm"
        code_graphics_mode3 = chr(27) + r"\[(3|4)\dm"
        code_graphics_mode4 = chr(27) + r"\[(9|10)[0-7]m"
        code_get_cursor_position = chr(27) + r"\[6n"
        code_cursor_position = chr(27) + r"\[m"
        code_attrs_off = chr(27) + r"\[0m"
        code_reverse = chr(27) + r"\[7m"
        code_cursor_left = chr(27) + r"\[\d+D"
        code_cursor_forward = chr(27) + r"\[\d*C"
        code_cursor_up = chr(27) + r"\[\d*A"
        code_cursor_down = chr(27) + r"\[\d*B"
        code_wrap_around = chr(27) + r"\[\?7h"
        code_enable_bracketed_paste_mode = chr(27) + r"\[\?2004h"
        code_disable_bracketed_paste_mode = chr(27) + r"\[\?2004l"
        code_underline = chr(27) + r"\[4m"
        code_query_device = chr(27) + r"\[c"

        code_set = [
            code_position_cursor,
            code_show_cursor,
            code_erase_line,
            code_enable_scroll,
            code_erase_start_line,
            code_carriage_return,
            code_disable_line_wrapping,
            code_erase_line_end,
            code_reset_mode_screen_options,
            code_reset_graphics_mode,
            code_erase_display,
            code_graphics_mode,
            code_graphics_mode1,
            code_graphics_mode2,
            code_graphics_mode3,
            code_graphics_mode4,
            code_get_cursor_position,
            code_cursor_position,
            code_erase_display,
            code_erase_display_0,
            code_attrs_off,
            code_reverse,
            code_cursor_left,
            code_cursor_up,
            code_cursor_down,
            code_cursor_forward,
            code_wrap_around,
            code_enable_bracketed_paste_mode,
            code_disable_bracketed_paste_mode,
            code_underline,
            code_query_device,
        ]

        output = string_buffer
        for ansi_esc_code in code_set:
            output = re.sub(ansi_esc_code, "", output)

        # CODE_NEXT_LINE must substitute with return
        output = re.sub(code_next_line, self.RETURN, output)

        # Aruba and ProCurve switches can use code_insert_line for <enter>
        insert_line_match = re.search(code_insert_line, output)
        if insert_line_match:
            # Substitute each insert_line with a new <enter>
            count = int(insert_line_match.group(1))
            output = re.sub(code_insert_line, count * self.RETURN, output)

        return output

    def cleanup(self, command: str = "") -> None:
        """Logout of the session on the network device plus any additional cleanup."""
        pass

    def paramiko_cleanup(self) -> None:
        """Cleanup Paramiko to try to gracefully handle SSH session ending."""
        if self.remote_conn_pre is not None:
            self.remote_conn_pre.close()
        del self.remote_conn_pre

    def disconnect(self) -> None:
        """Try to gracefully close the session."""
        try:
            self.cleanup()
        except Exception:
            # Keep going on cleanup process even if exceptions
            pass

        try:
            if self.protocol == "ssh":
                self.paramiko_cleanup()
            elif self.protocol == "telnet":
                assert isinstance(self.remote_conn, telnetlib.Telnet)
                self.remote_conn.close()  # type: ignore
            elif self.protocol == "serial":
                assert isinstance(self.remote_conn, serial.Serial)
                self.remote_conn.close()
        except Exception:
            # There have been race conditions observed on disconnect.
            pass
        finally:
            self.remote_conn_pre = None
            self.remote_conn = None
            if self.session_log:
                self.session_log.close()
            log.removeFilter(self._secrets_filter)

    def commit(self) -> str:
        """Commit method for platforms that support this."""
        raise AttributeError("Network device does not support 'commit()' method")

    def save_config(
        self, cmd: str = "", confirm: bool = False, confirm_response: str = ""
    ) -> str:
        """Not Implemented"""
        raise NotImplementedError

    def run_ttp(
        self,
        template: Union[str, bytes, "PathLike[Any]"],
        res_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Run TTP template parsing by using input parameters to collect
        devices output.

        :param template: template content, OS path to template or reference
            to template within TTP templates collection in
            ttp://path/to/template.txt format

        :param res_kwargs: ``**res_kwargs`` arguments to pass to TTP result method

        :param kwargs: any other ``**kwargs`` to use for TTP object instantiation

        TTP template must have inputs defined together with below parameters.

        :param method: name of Netmiko connection object method to call, default ``send_command``

        :param kwargs: Netmiko connection object method arguments

        :param commands: list of commands to collect

        Inputs' load could be of one of the supported formats and controlled by input's ``load``
        attribute, supported values - python, yaml or json. For each input output collected
        from device and parsed accordingly.
        """
        if res_kwargs is None:
            res_kwargs = {}
        return run_ttp_template(
            connection=self, template=template, res_kwargs=res_kwargs, **kwargs
        )


class TelnetConnection(BaseConnection):
    pass
