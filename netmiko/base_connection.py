"""
Base connection class for netmiko

Handles SSH connection and methods that are generically applicable to different
platforms (Cisco and non-Cisco).

Also defines methods that should generally be supported by child classes
"""
import io
import re
import time
from collections import deque
from os import path
from threading import Lock
import functools
from abc import ABC, abstractmethod
from typing import Optional, Dict, Callable, Any, Type

import paramiko
import serial
from tenacity import retry, stop_after_attempt, wait_exponential

from netmiko import log
from netmiko.netmiko_globals import BACKSPACE_CHAR
from netmiko.channel import SSHChannel, TelnetChannel, SerialChannel
from netmiko.session_log import SessionLog
from netmiko.ssh_exception import NetmikoTimeoutException
from netmiko.utilities import (
    check_serial_port,
    get_structured_data,
    get_structured_data_genie,
    get_structured_data_ttp,
    select_cmd_verify,
)
from netmiko.utilities import m_exec_time  # noqa


def lock_channel(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper_decorator(self: BaseConnection, *args: Any, **kwargs: Any) -> Any:
        self._lock_netmiko_session()
        try:
            return_val = func(self, *args, **kwargs)
        finally:
            # Always unlock the channel, even on exception.
            self._unlock_netmiko_session()
        return return_val

    return wrapper_decorator


class NetworkDevice(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    # Modify device behavior
    @abstractmethod
    def disable_paging(
        self,
        command: str,
        delay_factor: int = 1,
        cmd_verify: bool = True,
        pattern: Optional[str] = None,
    ) -> str:
        pass

    # Modify device behavior
    @abstractmethod
    def set_terminal_width(
        self,
        command: str,
        delay_factor: int = 1,
        cmd_verify: bool = False,
        pattern: Optional[str] = None,
    ) -> str:
        pass

    # Retrieve characteristic of device
    @abstractmethod
    def set_base_prompt(
        self,
        pri_prompt_terminator: str,
        alt_prompt_terminator: str,
        delay_factor: int = 1,
    ) -> str:
        pass

    # Retrieve characteristic of device
    @abstractmethod
    def find_prompt(self, delay_factor: int = 1) -> str:
        pass

    # Modify device (what is waiting to be read)
    @abstractmethod
    def clear_buffer(self, backoff: bool = True) -> None:
        pass

    # Read Device
    @abstractmethod
    def send_command_timing(
        self,
        command_string: str,
        delay_factor: int = 1,
        max_loops: int = 150,
        strip_prompt: bool = True,
        strip_command: bool = True,
        normalize: bool = True,
        use_textfsm: bool = False,
        textfsm_template: Optional[str] = None,
        use_ttp: bool = False,
        ttp_template: Optional[str] = None,
        use_genie: bool = False,
        cmd_verify: bool = False,
        cmd_echo: Optional[bool] = None,
    ) -> str:
        pass

    # Output processing
    @abstractmethod
    def strip_prompt(self, a_string: str) -> str:
        pass

    # Read Device
    @abstractmethod
    def send_command(
        self,
        command_string: str,
        expect_string: Optional[str] = None,
        delay_factor: int = 1,
        max_loops: int = 500,
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
    ) -> str:
        pass

    # Read device
    @abstractmethod
    def send_command_expect(self, *args: Any, **kwargs: Any) -> str:
        pass

    # Output processing
    @staticmethod
    @abstractmethod
    def strip_backspaces(output: str) -> str:
        pass

    # Output processing
    @abstractmethod
    def strip_command(self, command_string: str, output: str) -> str:
        pass

    # Output processing
    @abstractmethod
    def normalize_linefeeds(self, a_string: str) -> str:
        pass

    # Write preprocessing
    @abstractmethod
    def normalize_cmd(self, command: str) -> str:
        pass

    # State verification
    @abstractmethod
    def check_enable_mode(self, check_string: str = "") -> bool:
        pass

    # State change
    @abstractmethod
    def enable(
        self, cmd: str = "", pattern: str = "ssword", re_flags: int = re.IGNORECASE
    ) -> str:
        pass

    # State change
    @abstractmethod
    def exit_enable_mode(self, exit_command: str = "") -> str:
        pass

    # State verification
    @abstractmethod
    def check_config_mode(self, check_string: str = "", pattern: str = "") -> bool:
        pass

    # State change
    @abstractmethod
    def config_mode(
        self, config_command: str = "", pattern: str = "", re_flags: int = 0
    ) -> str:
        pass

    # State change
    @abstractmethod
    def exit_config_mode(self, exit_config: str = "", pattern: str = "") -> str:
        pass

    # Config Change
    @abstractmethod
    def send_config_from_file(
        self, config_file: Optional[str] = None, **kwargs: Any
    ) -> str:
        pass

    # Config Change
    @abstractmethod
    def send_config_set(
        self,
        config_commands: Optional[str] = None,
        exit_config_mode: bool = True,
        delay_factor: int = 1,
        max_loops: int = 150,
        strip_prompt: bool = False,
        strip_command: bool = False,
        config_mode_command: Optional[str] = None,
        cmd_verify: bool = True,
        enter_config_mode: bool = True,
    ) -> str:
        pass

    # Cleanup method
    @abstractmethod
    def cleanup(self, command: str = "") -> None:
        pass

    # Cleanup method
    @abstractmethod
    def disconnect(self) -> None:
        pass

    # Modify State / Apply Config
    @abstractmethod
    def commit(self) -> str:
        pass

    # Modify State / Apply Config
    @abstractmethod
    def save_config(self, *args: Any, **kwargs: Any) -> str:
        pass


class BaseConnection(object):
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
        global_cmd_verify: bool = None,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        pkey: Optional[paramiko.Pkey] = None,
        passphrase: Optional[str] = None,
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
        conn_timeout: int = 5,
        auth_timeout: Optional[int] = None,  # Timeout to wait for authentication response
        banner_timeout: int = 15,  # Timeout to wait for the banner to be presented (post TCP-connect)
        read_timeout: int = 10,  # Default timeout to wait for data in core read loop
        # Other timeouts
        # FIX - this will probably go away and read_timeout will replace
        blocking_timeout: int = 20,  # Read blocking timeout
        # FIX, not sure what to do here WRT to passing args from other libs and old timeout
        telnet_timeout: int = 20,
        timeout: int = 100,  # TCP connect timeout | overloaded to read-loop timeout
        session_timeout: int = 60,  # Used for locking/sharing the connection
        keepalive: int = 0,
        default_enter: Optional[str] = None,
        response_return: Optional[str] = None,
        serial_settings: Optional[Dict[str, Any]] = None,
        fast_cli: bool = False,
        _legacy_mode: bool = True,
        session_log: Optional[SessionLog] = None,
        session_log_record_writes: bool = False,
        session_log_file_mode: str = "write",
        allow_auto_change: bool = False,
        encoding: str = "ascii",
        sock: Optional[Any] = None,
        auto_connect: bool = True,
        telnet_channel: Type[TelnetChannel] = TelnetChannel,
    ) -> None:
        """
        Initialize attributes for establishing connection to target device.

        :param ip: IP address of target device. Not required if `host` is
            provided.
        :type ip: str

        :param host: Hostname of target device. Not required if `ip` is
                provided.
        :type host: str

        :param username: Username to authenticate against target device if
                required.
        :type username: str

        :param password: Password to authenticate against target device if
                required.
        :type password: str

        :param secret: The enable password if target device requires one.
        :type secret: str

        :param port: The destination port used to connect to the target
                device.
        :type port: int or None

        :param device_type: Class selection based on device type.
        :type device_type: str

        :param verbose: Enable additional messages to standard output.
        :type verbose: bool

        :param global_delay_factor: Multiplication factor affecting Netmiko delays (default: 1).
        :type global_delay_factor: int

        :param use_keys: Connect to target device using SSH keys.
        :type use_keys: bool

        :param key_file: Filename path of the SSH key file to use.
        :type key_file: str

        :param pkey: SSH key object to use.
        :type pkey: paramiko.PKey

        :param passphrase: Passphrase to use for encrypted key; password will be used for key
                decryption if not specified.
        :type passphrase: str

        :param allow_agent: Enable use of SSH key-agent.
        :type allow_agent: bool

        :param ssh_strict: Automatically reject unknown SSH host keys (default: False, which
                means unknown SSH host keys will be accepted).
        :type ssh_strict: bool

        :param system_host_keys: Load host keys from the users known_hosts file.
        :type system_host_keys: bool
        :param alt_host_keys: If `True` host keys will be loaded from the file specified in
                alt_key_file.
        :type alt_host_keys: bool

        :param alt_key_file: SSH host key file to use (if alt_host_keys=True).
        :type alt_key_file: str

        :param ssh_config_file: File name of OpenSSH configuration file.
        :type ssh_config_file: str

        :param timeout: Connection timeout.
        :type timeout: float

        :param session_timeout: Set a timeout for parallel requests.
        :type session_timeout: float

        :param auth_timeout: Set a timeout (in seconds) to wait for an authentication response.
        :type auth_timeout: float

        :param banner_timeout: Set a timeout to wait for the SSH banner (pass to Paramiko).
        :type banner_timeout: float

        :param keepalive: Send SSH keepalive packets at a specific interval, in seconds.
                Currently defaults to 0, for backwards compatibility (it will not attempt
                to keep the connection alive).
        :type keepalive: int

        :param default_enter: Character(s) to send to correspond to enter key (default: \n).
        :type default_enter: str

        :param response_return: Character(s) to use in normalized return data to represent
                enter key (default: \n)
        :type response_return: str

        :param fast_cli: Provide a way to optimize for performance. Converts select_delay_factor
                to select smallest of global and specific. Sets default global_delay_factor to .1
                (default: False)
        :type fast_cli: boolean

        :param session_log: File path or BufferedIOBase subclass object to write the session log to.
        :type session_log: str

        :param session_log_record_writes: The session log generally only records channel reads due
                to eliminate command duplication due to command echo. You can enable this if you
                want to record both channel reads and channel writes in the log (default: False).
        :type session_log_record_writes: boolean

        :param session_log_file_mode: "write" or "append" for session_log file mode
                (default: "write")
        :type session_log_file_mode: str

        :param allow_auto_change: Allow automatic configuration changes for terminal settings.
                (default: False)
        :type allow_auto_change: bool

        :param encoding: Encoding to be used when writing bytes to the output channel.
                (default: ascii)
        :type encoding: str

        :param sock: An open socket or socket-like object (such as a `.Channel`) to use for
                communication to the target host (default: None).
        :type sock: socket

        :param global_cmd_verify: Control whether command echo verification is enabled or disabled
                (default: None). Global attribute takes precedence over function `cmd_verify`
                argument. Value of `None` indicates to use function `cmd_verify` argument.
        :type global_cmd_verify: bool|None

        :param auto_connect: Control whether Netmiko automatically establishes the connection as
                part of the object creation (default: True).
        :type auto_connect: bool
        """
        self.channel = None
        self.telnet_channel = telnet_channel

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
        # FIX - eliminate this attribute and always strip ANSI codes
        self.ansi_escape_codes = False
        self.verbose = verbose
        self.auth_timeout = auth_timeout
        self.banner_timeout = banner_timeout
        self.read_timeout = read_timeout
        self.blocking_timeout = blocking_timeout
        self.conn_timeout = conn_timeout
        self.session_timeout = session_timeout
        self.timeout = timeout
        self.telnet_timeout = telnet_timeout
        self.keepalive = keepalive
        self.allow_auto_change = allow_auto_change
        self.encoding = encoding
        self.sock = sock

        # Netmiko will close the session_log if Netmiko opens the file
        self.session_log = None
        self._session_log_close = False
        if session_log is not None:
            no_log = {}
            if self.password:
                no_log["password"] = self.password
            if self.secret:
                no_log["secret"] = self.secret

            if isinstance(session_log, str):
                # If session_log is a string, open a file corresponding to string name.
                self.session_log = SessionLog(
                    file_name=session_log,
                    file_mode=session_log_file_mode,
                    file_encoding=encoding,
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
            else:
                raise ValueError(
                    "session_log must be a path to a file, a file handle, "
                    "or a BufferedIOBase subclass."
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

        self.fast_cli = fast_cli
        self._legacy_mode = _legacy_mode
        self.global_delay_factor = global_delay_factor
        self.global_cmd_verify = global_cmd_verify
        if self.fast_cli and self.global_delay_factor == 1:
            self.global_delay_factor = 0.1

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

            # Options for SSH Keys
            self.ssh_hostkey_args = {
                "system_host_keys": system_host_keys,
                "alt_host_keys": alt_host_keys,
                "alt_key_file": alt_key_file,
                "ssh_strict": ssh_strict,
            }

            self.use_keys = use_keys
            self.key_file = (
                path.abspath(path.expanduser(key_file)) if key_file else None
            )
            self.pkey = pkey
            self.passphrase = passphrase
            self.allow_agent = allow_agent

            # For SSH proxy support
            self.ssh_config_file = ssh_config_file

        # Establish the remote connection
        if auto_connect:
            self._open()

    def _open(
        self,
        ssh_channel_class: Optional[Type[SSHChannel]] = None,
        telnet_channel_class: Optional[Type[TelnetChannel]] = None,
        serial_channel_class: Optional[Type[SerialChannel]] = None,
    ) -> None:
        """Decouple connection creation from __init__ for mocking."""
        self._modify_connection_params()

        if self.protocol == "ssh":
            self._open_ssh(ssh_channel_class)
        elif self.protocol == "telnet":
            self._open_telnet(telnet_channel_class)
        elif self.protocol == "serial":
            self._open_serial(serial_channel_class)
        else:
            raise ValueError(f"Unknown protocol specified: {self.protocol}")

        self._try_session_preparation()

    def _open_ssh(self, ssh_channel_class: Optional[Type[SSHChannel]]) -> None:
        ssh_params = self._connect_params_dict()
        ChannelClass = SSHChannel if ssh_channel_class is None else ssh_channel_class
        self.channel = ChannelClass(
            ssh_params,
            device_type=self.device_type,
            ssh_hostkey_args=self.ssh_hostkey_args,
            encoding=self.encoding,
            session_log=self.session_log,
        )
        self.channel.establish_connection()
        self.special_login_handler()

    def _open_telnet(self, telnet_channel_class: Optional[Type[TelnetChannel]]) -> None:
        telnet_params = self._telnet_params_dict()
        ChannelClass = TelnetChannel if telnet_channel_class is None else telnet_channel_class
        # FIX: What is this about?
        # ChannelClass = self.telnet_channel
        self.channel = ChannelClass(
            telnet_params,
            device_type=self.device_type,
            encoding=self.encoding,
            session_log=self.session_log,
        )
        self.channel.establish_connection()

    def _open_serial(self, serial_channel_class: Optional[Type[SerialChannel]]) -> None:
        ChannelClass = (
            SerialChannel if serial_channel_class is None else serial_channel_class
        )
        self.channel = ChannelClass(
            self.serial_settings,
            device_type=self.device_type,
            encoding=self.encoding,
            session_log=self.session_log,
        )
        self.channel.establish_connection()

    def __enter__(self) -> BaseConnection:
        """Establish a session using a Context Manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Gracefully close connection on Context Manager exit."""
        self.disconnect()

    def _modify_connection_params(self) -> None:
        """Modify connection parameters prior to SSH connection."""
        pass

    def _timeout_exceeded(self, start: float, msg: str = "Timeout exceeded!"):
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
        """
        Try to acquire the Netmiko session lock. If not available, wait in the queue until
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
        """Release the channel at the end of the task."""
        if self._session_locker.locked():
            self._session_locker.release()

    @lock_channel
    def write_channel(self, out_data: str) -> None:
        """Wrapper function that will write data to the Channel class with locking."""
        self.channel.write_channel(out_data)

    @lock_channel
    def read_channel(self) -> str:
        """Wrapper function that will read all the available data from the Channel with locking."""
        return self.channel.read_channel()

    @lock_channel
    def read_channel_timing(self, delay_factor: int = 1, timeout: int = None) -> str:
        """Read data on the channel based on timing delays."""

        # Don't allow delay_factor to be less than one for delay_channel_timing.
        delay_factor = self.select_delay_factor(delay_factor)
        if delay_factor < 1:
            delay_factor = 1
        if timeout is None:
            timeout = self.read_timeout
        return self.channel.read_channel_timing(
            delay_factor=delay_factor, timeout=timeout
        )

    @lock_channel
    def read_until_prompt(self, timeout: int = None, re_flags: int = 0) -> str:
        """Read channel until self.base_prompt detected. Return ALL data available."""
        if timeout is None:
            timeout = self.read_timeout
        pattern = self.base_prompt
        return self.channel.read_channel_expect(
            pattern=pattern, timeout=timeout, re_flags=re_flags
        )

    @lock_channel
    def read_until_pattern(
        self, pattern: str, timeout: int = None, re_flags: int = 0
    ) -> str:
        """Read channel until pattern detected. Return ALL data available."""
        if timeout is None:
            timeout = self.read_timeout
        return self.channel.read_channel_expect(
            pattern=pattern, timeout=timeout, re_flags=re_flags
        )

    @lock_channel
    def read_until_prompt_or_pattern(
        self, pattern: str, timeout: int = None, re_flags: int = 0
    ) -> str:
        """Read until either self.base_prompt or pattern is detected."""
        prompt = re.escape(self.base_prompt)
        combined_pattern = r"({}|{})".format(prompt, pattern)
        return self.channel.read_channel_expect(
            pattern=combined_pattern, timeout=timeout, re_flags=re_flags
        )

    def is_alive(self) -> bool:
        """Wrapper function that the state of the communication channel."""
        return self.channel.is_alive()

    def serial_login(
        self,
        pri_prompt_terminator: str = r"#\s*$",
        alt_prompt_terminator: str = r">\s*$",
        username_pattern: str = r"(?:[Uu]ser:|sername|ogin)",
        pwd_pattern: str = r"assword",
        delay_factor: int = 1,
        max_loops: int = 20,
    ) -> str:
        # FIX: move to channel.py or somewhere else. Need to think about this and
        # telnet_login how they should be structured (too much code duplication).
        self.telnet_login(
            pri_prompt_terminator,
            alt_prompt_terminator,
            username_pattern,
            pwd_pattern,
            delay_factor,
            max_loops,
        )

    def _try_session_preparation(self) -> None:
        """
        In case of an exception happening during `session_preparation()` Netmiko should
        gracefully clean-up after itself. This might be challenging for library users
        to do since they do not have a reference to the object. This is possibly related
        to threads used in Paramiko.
        """
        try:
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
        self.set_terminal_width(command=cmd, pattern=cmd)
        self.disable_paging()
        self.set_base_prompt()
        """
        self._test_channel_read()
        self.set_base_prompt()
        self.set_terminal_width()
        self.disable_paging()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def _use_ssh_config(self, dict_arg: Dict[str, Any]) -> Dict[str, Any]:
        """Update SSH connection parameters based on contents of SSH config file.

        :param dict_arg: Dictionary of SSH connection parameters
        :type dict_arg: dict
        """
        # FIX: move to channel.py?
        # might need to stay here given how we are passing in a dictionary of arguments
        # to channel.py
        connect_dict = dict_arg.copy()

        # Use SSHConfig to generate source content.
        full_path = path.abspath(path.expanduser(self.ssh_config_file))
        if path.exists(full_path):
            ssh_config_instance = paramiko.SSHConfig()
            with io.open(full_path, "rt", encoding="utf-8") as f:
                ssh_config_instance.parse(f)
                source = ssh_config_instance.lookup(self.host)
        else:
            source = {}

        # Keys get normalized to lower-case
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
            "timeout": self.conn_timeout,
            "auth_timeout": self.auth_timeout,
            "banner_timeout": self.banner_timeout,
            "blocking_timeout": self.blocking_timeout,
            "keepalive": self.keepalive,
            "sock": self.sock,
        }

        # Check if using SSH 'config' file mainly for SSH proxy support
        if self.ssh_config_file:
            conn_dict = self._use_ssh_config(conn_dict)
        return conn_dict

    def _telnet_params_dict(self) -> Dict[str, Any]:
        """
        Generate dictionary of telnetlib connection parameters.

        Note: telnetlib describes it timeout as follows:

        'The optional timeout parameter specifies a timeout in seconds for blocking
        operations like the connection attempt'

        Consequently, need to map that most logically from Netmiko arguments and
        'conn_timeout' was chosen.
        """
        pri_prompt_terminator = r"#\s*$"
        alt_prompt_terminator = r">\s*$"
        username_pattern = r"(?:user:|username|login|user name)"
        pwd_pattern = r"assword"

        conn_dict = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "timeout": self.telnet_timeout,
            "pri_prompt_terminator": pri_prompt_terminator,
            "alt_prompt_terminator": alt_prompt_terminator,
            "username_pattern": username_pattern,
            "pwd_pattern": pwd_pattern,
        }

        return conn_dict

    def _sanitize_output(
        self, output: str, strip_command: bool = False, command_string: Optional[str] = None, strip_prompt: bool = False
    ) -> str:
        """Strip out command echo, trailing router prompt and ANSI escape codes.

        :param output: Output from a remote network device
        :type output: unicode string

        :param strip_command:
        :type strip_command:
        """
        output = self.normalize_linefeeds(output)
        if strip_command and command_string:
            command_string = self.normalize_linefeeds(command_string)
            output = self.strip_command(command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)
        return output

    def _test_channel_read(self, count: int = 40, pattern: str = "") -> str:
        """Try to read the channel (generally post login) verify you receive data back.

        :param count: the number of times to check the channel for data
        :type count: int

        :param pattern: Regular expression pattern used to determine end of channel read
        :type pattern: str
        """

        # FIX: move to channel.py and refactor?

        def _increment_delay(main_delay: float, increment: float = 1.1, maximum: int = 8) -> float:
            """Increment sleep time to a maximum value."""
            main_delay = main_delay * increment
            if main_delay >= maximum:
                main_delay = maximum
            return main_delay

        i = 0
        delay_factor = self.select_delay_factor(delay_factor=0)
        main_delay = delay_factor * 0.1
        time.sleep(main_delay * 10)
        new_data = ""
        while i <= count:
            new_data += self.read_channel_timing()
            if new_data and pattern:
                if re.search(pattern, new_data):
                    break
            elif new_data:
                break
            else:
                self.write_channel(self.RETURN)

            main_delay = _increment_delay(main_delay)
            time.sleep(main_delay)
            i += 1

        # check if data was ever present
        if new_data:
            return new_data
        else:
            raise NetmikoTimeoutException("Timed out waiting for data")

    def select_delay_factor(self, delay_factor):
        """
        Choose the greater of delay_factor or self.global_delay_factor (default).
        In fast_cli choose the lesser of delay_factor of self.global_delay_factor.

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """

        # FIX: what to do about this? Can global_delay_factor completely go away
        # and only be left with a delay_factor to send_command_timing?
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

    def special_login_handler(self, delay_factor=1):
        """Handler for devices like WLC, Extreme ERS that throw up characters prior to login."""
        pass

    def disable_paging(
        self, command="terminal length 0", delay_factor=1, cmd_verify=True, pattern=None
    ):
        """Disable paging default to a Cisco CLI method.

        :param command: Device command to disable pagination of output
        :type command: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        # FIX: NetworkDevice behavior should be stubbed out in ABC.
        # Should consider writing some common behavior that is more general than
        # disable_paging that could be used by set_terminal_width + disable_paging
        # + others.
        delay_factor = self.select_delay_factor(delay_factor)
        command = self.normalize_cmd(command)
        log.debug("In disable_paging")
        log.debug(f"Command: {command}")
        self.write_channel(command)
        # Make sure you read until you detect the command echo (avoid getting out of sync)
        if cmd_verify and self.global_cmd_verify is not False:
            output = self.read_until_pattern(pattern=re.escape(command.strip()))
        elif pattern:
            output = self.read_until_pattern(pattern=pattern)
        else:
            output = self.read_until_prompt()
        log.debug(f"{output}")
        log.debug("Exiting disable_paging")
        return output

    def set_terminal_width(
        self, command="", delay_factor=1, cmd_verify=False, pattern=None
    ):
        """CLI terminals try to automatically adjust the line based on the width of the terminal.
        This causes the output to get distorted when accessed programmatically.

        Set terminal width to 511 which works on a broad set of devices.

        :param command: Command string to send to the device
        :type command: str

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        # FIX: same as disable_paging (essentially)
        if not command:
            return ""
        delay_factor = self.select_delay_factor(delay_factor)
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

    # Retry by sleeping .33 and then double sleep until 5 attempts (.33, .66, 1.32, etc)
    @retry(
        wait=wait_exponential(multiplier=0.33, min=0, max=5), stop=stop_after_attempt(5)
    )
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
        # FIX: NetworkDevice behavior
        prompt = self.find_prompt(delay_factor=delay_factor)
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError(f"Router prompt not found: {repr(prompt)}")
        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]
        return self.base_prompt

    def find_prompt(self, delay_factor=1):
        """Finds the current network device prompt, last line only.

        :param delay_factor: See __init__: global_delay_factor
        :type delay_factor: int
        """
        # FIX: NetworkDevice behavior.
        # Not sure what to do about this / if anything.
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        self.write_channel(self.RETURN)
        sleep_time = delay_factor * 0.1
        time.sleep(sleep_time)

        # Initial attempt to get prompt
        prompt = self.read_channel().strip()

        # Check if the only thing you received was a newline
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
        prompt = self.normalize_linefeeds(prompt)
        prompt = prompt.split(self.RESPONSE_RETURN)[-1]
        prompt = prompt.strip()
        if not prompt:
            raise ValueError(f"Unable to find prompt: {prompt}")
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        log.debug(f"[find_prompt()]: prompt is {prompt}")
        return prompt

    def clear_buffer(self, backoff=True):
        """Read any data available in the channel."""
        # FIX: Move to channel.py. Can't we just call read_channel() and be done with it.
        # This is clear_buffer, plus delay with a backoff if there is more data present.
        sleep_time = 0.1 * self.global_delay_factor
        for _ in range(10):
            time.sleep(sleep_time)
            data = self.read_channel()
            if not data:
                break
            # Double sleep time each time we detect data
            log.debug("Clear buffer detects data in the channel")
            if backoff:
                sleep_time *= 2
                sleep_time = 3 if sleep_time >= 3 else sleep_time

    @select_cmd_verify
    def send_command_timing(
        self,
        command_string,
        delay_factor=1,
        max_loops=150,
        strip_prompt=True,
        strip_command=True,
        normalize=True,
        use_textfsm=False,
        textfsm_template=None,
        use_ttp=False,
        ttp_template=None,
        use_genie=False,
        cmd_verify=False,
        cmd_echo=None,
    ):
        """Execute command_string on the SSH channel using a delay-based mechanism. Generally
        used for show commands.

        :param command_string: The command to be executed on the remote device.
        :type command_string: str

        :param delay_factor: Multiplying factor used to adjust delays (default: 1).
        :type delay_factor: int or float

        :param max_loops: Controls wait time in conjunction with delay_factor. Will default to be
            based upon self.timeout.
        :type max_loops: int

        :param strip_prompt: Remove the trailing router prompt from the output (default: True).
        :type strip_prompt: bool

        :param strip_command: Remove the echo of the command from the output (default: True).
        :type strip_command: bool

        :param normalize: Ensure the proper enter is sent at end of command (default: True).
        :type normalize: bool

        :param use_textfsm: Process command output through TextFSM template (default: False).
        :type use_textfsm: bool

        :param textfsm_template: Name of template to parse output with; can be fully qualified
            path, relative path, or name of file in current directory. (default: None).
        :type textfsm_template: str

        :param use_ttp: Process command output through TTP template (default: False).
        :type use_ttp: bool

        :param ttp_template: Name of template to parse output with; can be fully qualified
            path, relative path, or name of file in current directory. (default: None).
        :type ttp_template: str

        :param use_genie: Process command output through PyATS/Genie parser (default: False).
        :type use_genie: bool

        :param cmd_verify: Verify command echo before proceeding (default: False).
        :type cmd_verify: bool

        :param cmd_echo: Deprecated (use cmd_verify instead)
        :type cmd_echo: bool
        """

        # FIX: NetworkDevice class. Maybe just move the low-level read_channel_timing into
        # here and completely get rid of that from the channel.py class.

        # For compatibility; remove cmd_echo in Netmiko 4.x.x
        if cmd_echo is not None:
            cmd_verify = cmd_echo

        output = ""

        delay_factor = self.select_delay_factor(delay_factor)
        # FIX: Cleanup in future versions of Netmiko
        if delay_factor < 1:
            if not self._legacy_mode and self.fast_cli:
                delay_factor = 1

        if normalize:
            command_string = self.normalize_cmd(command_string)

        self.write_channel(command_string)

        cmd = command_string.strip()
        # if cmd is just an "enter" skip this section
        if cmd and cmd_verify:
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            new_data = self.read_until_pattern(pattern=re.escape(cmd))
            new_data = self.normalize_linefeeds(new_data)

            # Strip off everything before the command echo
            if new_data.count(cmd) == 1:
                new_data = new_data.split(cmd)[1:]
                new_data = self.RESPONSE_RETURN.join(new_data)
                new_data = new_data.lstrip()
                output = f"{cmd}{self.RESPONSE_RETURN}{new_data}"
            else:
                # cmd is in the actual output (not just echoed)
                output = new_data

        log.debug(f"send_command_timing current output: {output}")

        # FIX: need to rationalized max_loops behavior (used to pass in here as an argument).
        output += self.read_channel_timing(delay_factor=delay_factor)
        output = self._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )

        # If both TextFSM, TTP and Genie are set, try TextFSM then TTP then Genie
        if use_textfsm:
            structured_output = get_structured_data(
                output,
                platform=self.device_type,
                command=command_string.strip(),
                template=textfsm_template,
            )
            # If we have structured data; return it.
            if not isinstance(structured_output, str):
                return structured_output
        if use_ttp:
            structured_output = get_structured_data_ttp(output, template=ttp_template)
            # If we have structured data; return it.
            if not isinstance(structured_output, str):
                return structured_output
        if use_genie:
            structured_output = get_structured_data_genie(
                output, platform=self.device_type, command=command_string.strip()
            )
            # If we have structured data; return it.
            if not isinstance(structured_output, str):
                return structured_output

        log.debug(f"send_command_timing final output: {output}")
        return output

    def strip_prompt(self, a_string):
        """Strip the trailing router prompt from the output.

        :param a_string: Returned string from device
        :type a_string: str
        """
        # FIX: Output/response processing in NetworkDevice class
        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]
        if self.base_prompt in last_line:
            return self.RESPONSE_RETURN.join(response_list[:-1])
        else:
            return a_string

    def _first_line_handler(self, data, search_pattern):
        """
        In certain situations the first line will get repainted which causes a false
        match on the terminating pattern.

        Filter this out.

        returns a tuple of (data, first_line_processed)

        Where data is the original data potentially with the first line modified
        and the first_line_processed is a flag indicating that we have handled the
        first line.
        """
        # FIX: have to look into this...
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

    @select_cmd_verify
    def send_command(
        self,
        command_string,
        expect_string=None,
        delay_factor=1,
        max_loops=500,
        auto_find_prompt=True,
        strip_prompt=True,
        strip_command=True,
        normalize=True,
        use_textfsm=False,
        textfsm_template=None,
        use_ttp=False,
        ttp_template=None,
        use_genie=False,
        cmd_verify=True,
    ):
        """Execute command_string on the SSH channel using a pattern-based mechanism. Generally
        used for show commands. By default this method will keep waiting to receive data until the
        network device prompt is detected. The current network device prompt will be determined
        automatically.

        :param command_string: The command to be executed on the remote device.
        :type command_string: str

        :param expect_string: Regular expression pattern to use for determining end of output.
            If left blank will default to being based on router prompt.
        :type expect_string: str

        :param delay_factor: Multiplying factor used to adjust delays (default: 1).
        :type delay_factor: int

        :param max_loops: Controls wait time in conjunction with delay_factor. Will default to be
            based upon self.timeout.
        :type max_loops: int

        :param strip_prompt: Remove the trailing router prompt from the output (default: True).
        :type strip_prompt: bool

        :param strip_command: Remove the echo of the command from the output (default: True).
        :type strip_command: bool

        :param normalize: Ensure the proper enter is sent at end of command (default: True).
        :type normalize: bool

        :param use_textfsm: Process command output through TextFSM template (default: False).
        :type normalize: bool

        :param textfsm_template: Name of template to parse output with; can be fully qualified
            path, relative path, or name of file in current directory. (default: None).

        :param use_ttp: Process command output through TTP template (default: False).
        :type use_ttp: bool

        :param ttp_template: Name of template to parse output with; can be fully qualified
            path, relative path, or name of file in current directory. (default: None).
        :type ttp_template: str

        :param use_genie: Process command output through PyATS/Genie parser (default: False).
        :type normalize: bool

        :param cmd_verify: Verify command echo before proceeding (default: True).
        :type cmd_verify: bool
        """

        # FIX: NetworkDevice class. Should rationalize the behavior.
        # Probably should move parts of this into other functions (like all of the
        # structured data handling)

        # Time to delay in each read loop
        loop_delay = 0.2

        # Default to making loop time be roughly equivalent to self.timeout (support old max_loops
        # and delay_factor arguments for backwards compatibility).
        delay_factor = self.select_delay_factor(delay_factor)
        if delay_factor == 1 and max_loops == 500:
            # Default arguments are being used; use self.timeout instead
            max_loops = int(self.timeout / loop_delay)

        # Find the current router prompt
        if expect_string is None:
            if auto_find_prompt:
                try:
                    prompt = self.find_prompt(delay_factor=delay_factor)
                except ValueError:
                    prompt = self.base_prompt
            else:
                prompt = self.base_prompt
            search_pattern = re.escape(prompt.strip())
        else:
            search_pattern = expect_string

        if normalize:
            command_string = self.normalize_cmd(command_string)

        time.sleep(delay_factor * loop_delay)
        self.clear_buffer()
        self.write_channel(command_string)
        new_data = ""

        cmd = command_string.strip()
        # if cmd is just an "enter" skip this section
        if cmd and cmd_verify:
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            new_data = self.read_until_pattern(pattern=re.escape(cmd))
            new_data = self.normalize_linefeeds(new_data)
            # Strip off everything before the command echo (to avoid false positives on the prompt)
            if new_data.count(cmd) == 1:
                new_data = new_data.split(cmd)[1:]
                new_data = self.RESPONSE_RETURN.join(new_data)
                new_data = new_data.lstrip()
                new_data = f"{cmd}{self.RESPONSE_RETURN}{new_data}"

        i = 1
        output = ""
        past_three_reads = deque(maxlen=3)
        first_line_processed = False

        # Keep reading data until search_pattern is found or until max_loops is reached.
        while i <= max_loops:
            if new_data:
                output += new_data
                past_three_reads.append(new_data)

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
                    # Check if pattern is in the past three reads
                    if re.search(search_pattern, "".join(past_three_reads)):
                        break

            time.sleep(delay_factor * loop_delay)
            i += 1
            new_data = self.read_channel()
        else:  # nobreak
            raise IOError(
                "Search pattern never detected in send_command: {}".format(
                    search_pattern
                )
            )

        output = self._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )

        # If both TextFSM, TTP and Genie are set, try TextFSM then TTP then Genie
        if use_textfsm:
            structured_output = get_structured_data(
                output,
                platform=self.device_type,
                command=command_string.strip(),
                template=textfsm_template,
            )
            # If we have structured data; return it.
            if not isinstance(structured_output, str):
                return structured_output
        if use_ttp:
            structured_output = get_structured_data_ttp(output, template=ttp_template)
            # If we have structured data; return it.
            if not isinstance(structured_output, str):
                return structured_output
        if use_genie:
            structured_output = get_structured_data_genie(
                output, platform=self.device_type, command=command_string.strip()
            )
            # If we have structured data; return it.
            if not isinstance(structured_output, str):
                return structured_output
        return output

    def send_command_expect(self, *args, **kwargs):
        """Support previous name of send_command method.

        :param args: Positional arguments to send to send_command()
        :type args: list

        :param kwargs: Keyword arguments to send to send_command()
        :type kwargs: dict
        """
        return self.send_command(*args, **kwargs)

    @staticmethod
    def strip_backspaces(output):
        """Strip any backspace characters out of the output.

        :param output: Output obtained from a remote network device.
        :type output: str
        """
        # FIX: output/response handling from devices
        backspace_char = "\x08"
        return output.replace(backspace_char, "")

    def strip_command(self, command_string, output):
        """
        Strip command_string from output string

        Cisco IOS adds backspaces into output for long commands (i.e. for commands that line wrap)

        :param command_string: The command string sent to the device
        :type command_string: str

        :param output: The returned output as a result of the command string sent to the device
        :type output: str
        """
        # FIX: output/response handling from devices
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

    def normalize_linefeeds(self, a_string):
        """Convert `\r\r\n`,`\r\n`, `\n\r` to `\n.`

        :param a_string: A string that may have non-normalized line feeds
            i.e. output returned from device, or a device prompt
        :type a_string: str
        """
        # FIX: output/response handling from devices
        newline = re.compile("(\r\r\r\n|\r\r\n|\r\n|\n\r)")
        a_string = newline.sub(self.RESPONSE_RETURN, a_string)
        if self.RESPONSE_RETURN == "\n":
            # Convert any remaining \r to \n
            return re.sub("\r", self.RESPONSE_RETURN, a_string)
        else:
            return a_string

    def normalize_cmd(self, command):
        """Normalize CLI commands to have a single trailing newline.

        :param command: Command that may require line feed to be normalized
        :type command: str
        """
        # FIX: write_channel preprocessing for devices
        command = command.rstrip()
        command += self.RETURN
        return command

    def check_enable_mode(self, check_string=""):
        """Check if in enable mode. Return boolean.

        :param check_string: Identification of privilege mode from device
        :type check_string: str
        """
        # FIX: NetworkDevice class
        self.write_channel(self.RETURN)
        output = self.read_until_prompt()
        return check_string in output

    def enable(self, cmd="", pattern="ssword", re_flags=re.IGNORECASE):
        """Enter enable mode.

        :param cmd: Device command to enter enable mode
        :type cmd: str

        :param pattern: pattern to search for indicating device is waiting for password
        :type pattern: str

        :param re_flags: Regular expression flags used in conjunction with pattern
        :type re_flags: int
        """
        # FIX: NetworkDevice class
        output = ""
        msg = (
            "Failed to enter enable mode. Please ensure you pass "
            "the 'secret' argument to ConnectHandler."
        )
        if not self.check_enable_mode():
            self.write_channel(self.normalize_cmd(cmd))
            try:
                output += self.read_until_prompt_or_pattern(
                    pattern=pattern, re_flags=re_flags
                )
                self.write_channel(self.normalize_cmd(self.secret))
                output += self.read_until_prompt()
            except NetmikoTimeoutException:
                raise ValueError(msg)
            if not self.check_enable_mode():
                raise ValueError(msg)
        return output

    def exit_enable_mode(self, exit_command=""):
        """Exit enable mode.

        :param exit_command: Command that exits the session from privileged mode
        :type exit_command: str
        """
        # FIX: NetworkDevice class
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            output += self.read_until_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def check_config_mode(self, check_string="", pattern=""):
        """Checks if the device is in configuration mode or not.

        :param check_string: Identification of configuration mode from the device
        :type check_string: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str
        """
        # FIX: NetworkDevice class
        self.write_channel(self.RETURN)
        # You can encounter an issue here (on router name changes) prefer delay-based solution
        if not pattern:
            output = self.read_channel_timing()
        else:
            output = self.read_until_pattern(pattern=pattern)
        return check_string in output

    def config_mode(self, config_command="", pattern="", re_flags=0):
        """Enter into config_mode.

        :param config_command: Configuration command to send to the device
        :type config_command: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str

        :param re_flags: Regular expression flags
        :type re_flags: RegexFlag
        """
        # FIX: NetworkDevice class
        output = ""
        if not self.check_config_mode():
            self.write_channel(self.normalize_cmd(config_command))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(config_command.strip())
                )
            if not re.search(pattern, output, flags=re_flags):
                output += self.read_until_pattern(pattern=pattern, re_flags=re_flags)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode.")
        return output

    def exit_config_mode(self, exit_config="", pattern=""):
        """Exit from configuration mode.

        :param exit_config: Command to exit configuration mode
        :type exit_config: str

        :param pattern: Pattern to terminate reading of channel
        :type pattern: str
        """
        # FIX: NetworkDevice class
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            # Make sure you read until you detect the command echo (avoid getting out of sync)
            if self.global_cmd_verify is not False:
                output += self.read_until_pattern(
                    pattern=re.escape(exit_config.strip())
                )
            if not re.search(pattern, output, flags=re.M):
                output += self.read_until_pattern(pattern=pattern)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        log.debug(f"exit_config_mode: {output}")
        return output

    def send_config_from_file(self, config_file=None, **kwargs):
        """
        Send configuration commands down the SSH channel from a file.

        The file is processed line-by-line and each command is sent down the
        SSH channel.

        **kwargs are passed to send_config_set method.

        :param config_file: Path to configuration file to be sent to the device
        :type config_file: str

        :param kwargs: params to be sent to send_config_set method
        :type kwargs: dict
        """
        # FIX: NetworkDevice class
        with io.open(config_file, "rt", encoding="utf-8") as cfg_file:
            return self.send_config_set(cfg_file, **kwargs)

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
        enter_config_mode=True,
    ):
        """
        Send configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Automatically exits/enters configuration mode.

        :param config_commands: Multiple configuration commands to be sent to the device
        :type config_commands: list or string

        :param exit_config_mode: Determines whether or not to exit config mode after complete
        :type exit_config_mode: bool

        :param delay_factor: Factor to adjust delays
        :type delay_factor: int

        :param max_loops: Controls wait time in conjunction with delay_factor (default: 150)
        :type max_loops: int

        :param strip_prompt: Determines whether or not to strip the prompt
        :type strip_prompt: bool

        :param strip_command: Determines whether or not to strip the command
        :type strip_command: bool

        :param config_mode_command: The command to enter into config mode
        :type config_mode_command: str

        :param cmd_verify: Whether or not to verify command echo for each command in config_set
        :type cmd_verify: bool

        :param enter_config_mode: Do you enter config mode before sending config commands
        :type exit_config_mode: bool

        """
        # FIX: NetworkDevice class
        delay_factor = self.select_delay_factor(delay_factor)
        if config_commands is None:
            return ""
        elif isinstance(config_commands, str):
            config_commands = (config_commands,)

        if not hasattr(config_commands, "__iter__"):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        output = ""
        if enter_config_mode:
            cfg_mode_args = (config_mode_command,) if config_mode_command else tuple()
            output += self.config_mode(*cfg_mode_args)

        if self.fast_cli and self._legacy_mode:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))
            # Gather output
            output += self.read_channel_timing(
                delay_factor=delay_factor, max_loops=max_loops
            )
        elif not cmd_verify:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))
                time.sleep(delay_factor * 0.05)
            # Gather output
            output += self.read_channel_timing(
                delay_factor=delay_factor, max_loops=max_loops
            )
        else:
            for cmd in config_commands:
                self.write_channel(self.normalize_cmd(cmd))

                # Make sure command is echoed
                new_output = self.read_until_pattern(pattern=re.escape(cmd.strip()))
                output += new_output

                # We might capture next prompt in the original read
                pattern = f"(?:{re.escape(self.base_prompt)}|#)"
                if not re.search(pattern, new_output):
                    # Make sure trailing prompt comes back (after command)
                    # NX-OS has fast-buffering problem where it immediately echoes command
                    # Even though the device hasn't caught up with processing command.
                    new_output = self.read_until_pattern(pattern=pattern)
                    output += new_output

        if exit_config_mode:
            output += self.exit_config_mode()
        output = self._sanitize_output(output)
        log.debug(f"{output}")
        return output

    def cleanup(self, command=""):
        """Logout of the session on the network device plus any additional cleanup."""
        # FIX: NetworkDevice class
        pass

    def disconnect(self):
        """
        Try to gracefully close the session:

        Should do the following:
        1. Gracefully disconnect from device (right now in "cleanup" method)
        2. Should close the channel / cleanup the channel
        3. Should close the Session Log
        """
        # FIX: NetworkDevice class
        try:
            self.cleanup()
        except Exception:
            # There have been race conditions observed on disconnect.
            pass
        finally:
            self.channel.close()
            if self.session_log:
                self.session_log.close()

    def commit(self):
        """Commit method for platforms that support this."""
        # FIX: NetworkDevice class
        raise AttributeError("Network device does not support 'commit()' method")

    def save_config(self, *args, **kwargs):
        # FIX: NetworkDevice class
        """Not Implemented"""
        raise NotImplementedError


class TelnetConnection(BaseConnection):
    pass
