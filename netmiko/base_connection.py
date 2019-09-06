"""
Base connection class for netmiko

Handles SSH connection and methods that are generically applicable to different
platforms (Cisco and non-Cisco).

Also defines methods that should generally be supported by child classes
"""

from __future__ import print_function
from __future__ import unicode_literals

import io
import re
import socket
import telnetlib
import time
from collections import deque
from os import path
from threading import Lock

import paramiko
import serial

from netmiko import log
from netmiko.netmiko_globals import MAX_BUFFER, BACKSPACE_CHAR
from netmiko.py23_compat import string_types, bufferedio_types, text_type
from netmiko.ssh_exception import (
    NetMikoTimeoutException,
    NetMikoAuthenticationException,
)
from netmiko.utilities import (
    write_bytes,
    check_serial_port,
    get_structured_data,
    get_structured_data_genie,
)


class BaseConnection(object):
    """
    Defines vendor independent methods.

    Otherwise method left as a stub method.
    """

    def __init__(
        self,
        ip="",
        host="",
        username="",
        password=None,
        secret="",
        port=None,
        device_type="",
        verbose=False,
        global_delay_factor=1,
        use_keys=False,
        key_file=None,
        pkey=None,
        passphrase=None,
        allow_agent=False,
        ssh_strict=False,
        system_host_keys=False,
        alt_host_keys=False,
        alt_key_file="",
        ssh_config_file=None,
        timeout=100,
        session_timeout=60,
        auth_timeout=None,
        blocking_timeout=8,
        banner_timeout=5,
        keepalive=0,
        default_enter=None,
        response_return=None,
        serial_settings=None,
        fast_cli=False,
        session_log=None,
        session_log_record_writes=False,
        session_log_file_mode="write",
        allow_auto_change=False,
        encoding="ascii",
    ):
        r"""
        Initialize attributes for establishing connection to target device.

        Args:
            ip (str): IP address of target device. Not required if `host` is provided.
            host (str): Hostname of target device. Not required if `ip` is provided.
            username (str): Username to authenticate against target device if required.
            password (str): Password to authenticate against target device if required.
            secret (str): The enable password if target device requires one.
            port (int or None): The destination port used to connect to the target device.
            device_type (str): Class selection based on device type.
            verbose (bool): Enable additional messages to standard output.
            global_delay_factor (int): Multiplication factor affecting Netmiko delays (default: 1).
            use_keys (bool): Connect to target device using SSH keys.
            key_file (str): Filename path of the SSH key file to use.
            pkey (paramiko.PKey): SSH key object to use.
            passphrase (str): Passphrase to use for encrypted key; password will be used for key
                decryption if not specified.
            allow_agent (bool): Enable use of SSH key-agent.
            ssh_strict (bool): Automatically reject unknown SSH host keys (default: False, which
                means unknown SSH host keys will be accepted).
            system_host_keys (bool): Load host keys from the users known_hosts file.
            alt_host_keys (str): If `True` host keys will be loaded from the file specified in
                alt_key_file.
            alt_host_keys (bool): provide alternate keys
            alt_key_file (str): SSH host key file to use (if alt_host_keys=True).
            ssh_config_file (str): File name of OpenSSH configuration file.
            timeout (float): Connection timeout.
            session_timeout (float): Set a timeout for parallel requests.
            auth_timeout (float): Set a timeout (in seconds) to wait for an authentication response.
            blocking_timeout (float): timeout for channel read under certain circumstances
            banner_timeout (float): Set a timeout to wait for the SSH banner (pass to Paramiko).
            keepalive(int): Send SSH keepalive packets at a specific interval, in seconds.
                Currently defaults to 0, for backwards compatibility (it will not attempt
                to keep the connection alive).
            default_enter (str): Character(s) to send to correspond to enter key (default: \n).
            response_return (str): Character(s) to use in normalized return data to represent
                enter key (default: \n)
            serial_settings (dict): dictionary defining settings to be used for serial connection
            fast_cli (bool): Provide a way to optimize for performance. Converts select_delay_factor
                to select smallest of global and specific. Sets default global_delay_factor to .1
                (default: False)
            session_log (str): File/path or BufferedIOBase object to write the session log to.
            session_log_record_writes (bool): The session log generally only records channel reads
                due to eliminate command duplication due to command echo. You can enable this if you
                want to record both channel reads and channel writes in the log (default: False).
            session_log_file_mode (str): "write" or "append" for session_log file mode
                (default: write)
            allow_auto_change (bool): Allow automatic configuration changes for terminal settings.
                (default: False)
            encoding (str): Encoding to be used when writing bytes to the output channel.
                (default: ascii)

        """
        self.remote_conn = None

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
        self.ansi_escape_codes = False
        self.verbose = verbose
        self.timeout = timeout
        self.auth_timeout = auth_timeout
        self.banner_timeout = banner_timeout
        self.session_timeout = session_timeout
        self.blocking_timeout = blocking_timeout
        self.keepalive = keepalive
        self.allow_auto_change = allow_auto_change
        self.encoding = encoding

        # Netmiko will close the session_log if we open the file
        self.session_log = None
        self.session_log_record_writes = session_log_record_writes
        self._session_log_close = False
        # Ensures last write operations prior to disconnect are recorded.
        self._session_log_fin = False
        if session_log is not None:
            if isinstance(session_log, string_types):
                # If session_log is a string, open a file corresponding to string name.
                self.open_session_log(filename=session_log, mode=session_log_file_mode)
            elif isinstance(session_log, bufferedio_types):
                # In-memory buffer or an already open file handle
                self.session_log = session_log
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
        self.global_delay_factor = global_delay_factor
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

            if not ssh_strict:
                self.key_policy = paramiko.AutoAddPolicy()
            else:
                self.key_policy = paramiko.RejectPolicy()

            # Options for SSH host_keys
            self.use_keys = use_keys
            self.key_file = key_file
            self.pkey = pkey
            self.passphrase = passphrase
            self.allow_agent = allow_agent
            self.system_host_keys = system_host_keys
            self.alt_host_keys = alt_host_keys
            self.alt_key_file = alt_key_file

            # For SSH proxy support
            self.ssh_config_file = ssh_config_file

        # Establish the remote connection
        self._open()

    def _open(self):
        """Decouple connection creation from __init__ for mocking."""
        self._modify_connection_params()
        self.establish_connection()
        self._try_session_preparation()

    def __enter__(self):
        """Establish a session using a Context Manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Gracefully close connection on Context Manager exit.

        Args:
            exc_type: execption type being raised
            exc_value: message from exception being raised
            traceback: traceback from exception being raised

        """
        self.disconnect()

    def _modify_connection_params(self):
        """Modify connection parameters prior to SSH connection."""
        pass

    def _timeout_exceeded(self, start, msg="Timeout exceeded!"):
        """
        Raise NetMikoTimeoutException if waiting too much in the serving queue.

        Args:
            start (float): Initial start time to see if session lock timeout has been exceeded
            msg (str): Exception message if timeout was exceeded

        Raises:
            NetMikoTimeoutException: if timeout exceeded

        Returns:
            bool: False if timeout not exceeded

        """
        if not start:
            # Must provide a comparison time
            return False
        if time.time() - start > self.session_timeout:
            # session_timeout exceeded
            raise NetMikoTimeoutException(msg)
        return False

    def _lock_netmiko_session(self, start=None):
        """
        Acquire session lock.

        Try to acquire the Netmiko session lock. If not available, wait in the queue until
        the channel is available again.

        Args:
            start (float): Initial start time to measure the session timeout

        Returns:
            bool: True if successful

        """
        if not start:
            start = time.time()
        # Wait here until the SSH channel lock is acquired or until session_timeout exceeded
        while not self._session_locker.acquire(False) and not self._timeout_exceeded(
            start, "The netmiko channel is not available!"
        ):
            time.sleep(0.1)
        return True

    def _unlock_netmiko_session(self):
        """Release the channel at the end of the task."""
        if self._session_locker.locked():
            self._session_locker.release()

    def _write_channel(self, out_data):
        """
        Generic handler that will write to both SSH and telnet channel.

        Args:
            out_data (str): data to be written to the channel

        Raises:
            ValueError: if invalid connection type

        """
        if self.protocol == "ssh":
            self.remote_conn.sendall(write_bytes(out_data, encoding=self.encoding))
        elif self.protocol == "telnet":
            self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))
        elif self.protocol == "serial":
            self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))
            self.remote_conn.flush()
        else:
            raise ValueError("Invalid protocol specified")
        try:
            log.debug(
                "write_channel: {}".format(
                    write_bytes(out_data, encoding=self.encoding)
                )
            )
            if self._session_log_fin or self.session_log_record_writes:
                self._write_session_log(out_data)
        except UnicodeDecodeError:
            # Don't log non-ASCII characters; this is null characters and telnet IAC (PY2)
            pass

    def _write_session_log(self, data):
        if self.session_log is not None and len(data) > 0:
            # Hide the password and secret in the session_log
            if self.password:
                data = data.replace(self.password, "********")
            if self.secret:
                data = data.replace(self.secret, "********")
            self.session_log.write(write_bytes(data, encoding=self.encoding))
            self.session_log.flush()

    def write_channel(self, out_data):
        """
        Generic handler that will write to both SSH and telnet channel.

        Args:
            out_data (str): data to be written to the channel

        """
        self._lock_netmiko_session()
        try:
            self._write_channel(out_data)
        finally:
            # Always unlock the SSH channel, even on exception.
            self._unlock_netmiko_session()

    def is_alive(self):
        """
        Returns a boolean flag with the state of the connection.

        Returns:
            bool: True/False if device alive or not

        """
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
                self.remote_conn.sock.sendall(telnetlib.IAC + telnetlib.NOP)
                self.remote_conn.sock.sendall(telnetlib.IAC + telnetlib.NOP)
                self.remote_conn.sock.sendall(telnetlib.IAC + telnetlib.NOP)
                return True
            except AttributeError:
                return False
        else:
            # SSH
            try:
                # Try sending ASCII null byte to maintain the connection alive
                log.debug("Sending the NULL byte")
                self.write_channel(null)
                return self.remote_conn.transport.is_active()
            except (socket.error, EOFError):
                log.error("Unable to send", exc_info=True)
                # If unable to send, we can tell for sure that the connection is unusable
                return False
        return False

    def _read_channel(self):
        """Generic handler that will read all the data from an SSH or telnet channel."""
        if self.protocol == "ssh":
            output = ""
            while True:
                if self.remote_conn.recv_ready():
                    outbuf = self.remote_conn.recv(MAX_BUFFER)
                    if len(outbuf) == 0:
                        raise EOFError("Channel stream closed by remote device.")
                    output += outbuf.decode("utf-8", "ignore")
                else:
                    break
        elif self.protocol == "telnet":
            output = self.remote_conn.read_very_eager().decode("utf-8", "ignore")
        elif self.protocol == "serial":
            output = ""
            while self.remote_conn.in_waiting > 0:
                output += self.remote_conn.read(self.remote_conn.in_waiting).decode(
                    "utf-8", "ignore"
                )
        log.debug("read_channel: {}".format(output))
        self._write_session_log(output)
        return output

    def read_channel(self):
        """Generic handler that will read all the data from an SSH or telnet channel."""
        output = ""
        self._lock_netmiko_session()
        try:
            output = self._read_channel()
        finally:
            # Always unlock the SSH channel, even on exception.
            self._unlock_netmiko_session()
        return output

    def _read_channel_expect(self, pattern="", re_flags=0, max_loops=150):
        """
        Function that reads channel until pattern is detected.

        pattern takes a regular expression.

        By default pattern will be self.base_prompt

        Note: this currently reads beyond pattern. In the case of SSH it reads MAX_BUFFER.
        In the case of telnet it reads all non-blocking data.

        There are dependencies here like determining whether in config_mode that are actually
        depending on reading beyond pattern.

        Args:
            pattern (str): Regular expression pattern used to identify the command is done
                (defaults to self.base_prompt)
            re_flags (int): regex flags used in conjunction with pattern to search for prompt
                (defaults to no flags)
            max_loops (int): max number of iterations to read the channel before raising exception.
                Will default to be based upon self.timeout.

        """
        output = ""
        if not pattern:
            pattern = re.escape(self.base_prompt)
        log.debug("Pattern is: {}".format(pattern))

        i = 1
        loop_delay = 0.1
        # Default to making loop time be roughly equivalent to self.timeout (support old max_loops
        # argument for backwards compatibility).
        if max_loops == 150:
            max_loops = int(self.timeout / loop_delay)
        while i < max_loops:
            if self.protocol == "ssh":
                try:
                    # If no data available will wait timeout seconds trying to read
                    self._lock_netmiko_session()
                    new_data = self.remote_conn.recv(MAX_BUFFER)
                    if len(new_data) == 0:
                        raise EOFError("Channel stream closed by remote device.")
                    new_data = new_data.decode("utf-8", "ignore")
                    log.debug("_read_channel_expect read_data: {}".format(new_data))
                    output += new_data
                    self._write_session_log(new_data)
                except socket.timeout:
                    raise NetMikoTimeoutException(
                        "Timed-out reading channel, data not available."
                    )
                finally:
                    self._unlock_netmiko_session()
            elif self.protocol == "telnet" or "serial":
                output += self.read_channel()
            if re.search(pattern, output, flags=re_flags):
                log.debug("Pattern found: {} {}".format(pattern, output))
                return output
            time.sleep(loop_delay * self.global_delay_factor)
            i += 1
        raise NetMikoTimeoutException(
            "Timed-out reading channel, pattern not found in output: {}".format(pattern)
        )

    def _read_channel_timing(self, delay_factor=1, max_loops=150):
        """
        Read data on the channel based on timing delays.

        Attempt to read channel max_loops number of times. If no data this will cause a 15 second
        delay.

        Once data is encountered read channel for another two seconds (2 * delay_factor) to make
        sure reading of channel is complete.

        Args:
            delay_factor (int): multiplicative factor to adjust delay when reading channel (delays
                get multiplied by this factor)
            max_loops (int): maximum number of loops to iterate through before returning channel data.
                Will default to be based upon self.timeout.

        """
        # Time to delay in each read loop
        loop_delay = 0.1
        final_delay = 2

        # Default to making loop time be roughly equivalent to self.timeout (support old max_loops
        # and delay_factor arguments for backwards compatibility).
        delay_factor = self.select_delay_factor(delay_factor)
        if delay_factor == 1 and max_loops == 150:
            max_loops = int(self.timeout / loop_delay)

        channel_data = ""
        i = 0
        while i <= max_loops:
            time.sleep(loop_delay * delay_factor)
            new_data = self.read_channel()
            if new_data:
                channel_data += new_data
            else:
                # Safeguard to make sure really done
                time.sleep(final_delay * delay_factor)
                new_data = self.read_channel()
                if not new_data:
                    break
                else:
                    channel_data += new_data
            i += 1
        return channel_data

    def read_until_prompt(self, *args, **kwargs):
        """
        Read channel until self.base_prompt detected. Return ALL data available.

        Args:
            *args: positional args
            **kwargs: keyword args

        Returns:
            data: channel read data

        """
        return self._read_channel_expect(*args, **kwargs)

    def read_until_pattern(self, *args, **kwargs):
        """
        Read channel until pattern detected. Return ALL data available.

        Args:
            *args: positional args
            **kwargs: keyword args

        Returns:
            data: channel read data

        """
        return self._read_channel_expect(*args, **kwargs)

    def read_until_prompt_or_pattern(self, pattern="", re_flags=0):
        """
        Read until either self.base_prompt or pattern is detected.

        Args:
            pattern (str): the pattern used to identify that the output is complete (i.e. stop
                reading when pattern is detected). pattern will be combined with self.base_prompt to
                terminate output reading when the first of self.base_prompt or pattern is detected.
            re_flags (int): regex flags used in conjunction with pattern to search for prompt
                (defaults to no flags)

        """
        combined_pattern = re.escape(self.base_prompt)
        if pattern:
            combined_pattern = r"({}|{})".format(combined_pattern, pattern)
        return self._read_channel_expect(combined_pattern, re_flags=re_flags)

    def serial_login(
        self,
        pri_prompt_terminator=r"#\s*$",
        alt_prompt_terminator=r">\s*$",
        username_pattern=r"(?:[Uu]ser:|sername|ogin)",
        pwd_pattern=r"assword",
        delay_factor=1,
        max_loops=20,
    ):
        """
        Serial login.

        Args:
            pri_prompt_terminator (str): string of primary prompt terminator
            alt_prompt_terminator (str): string of alternate prompt terminator
            username_pattern (str): pattern of username prompt
            pwd_pattern (str): pattern of password prompt
            delay_factor (int): delay factor value
            max_loops (int): max loops

        """
        self.telnet_login(
            pri_prompt_terminator,
            alt_prompt_terminator,
            username_pattern,
            pwd_pattern,
            delay_factor,
            max_loops,
        )

    def telnet_login(
        self,
        pri_prompt_terminator=r"#\s*$",
        alt_prompt_terminator=r">\s*$",
        username_pattern=r"(?:user:|username|login|user name)",
        pwd_pattern=r"assword",
        delay_factor=1,
        max_loops=20,
    ):
        """
        Telnet login. Can be username/password or just password.

        Args:
            pri_prompt_terminator (str): string of primary prompt terminator
            alt_prompt_terminator (str): string of alternate prompt terminator
            username_pattern (str): pattern of username prompt
            pwd_pattern (str): pattern of password prompt
            delay_factor (int): delay factor value
            max_loops (int): max loops

        """
        delay_factor = self.select_delay_factor(delay_factor)
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
                    self.write_channel(self.username + self.TELNET_RETURN)
                    time.sleep(1 * delay_factor)
                    output = self.read_channel()
                    return_msg += output

                # Search for password pattern / send password
                if re.search(pwd_pattern, output, flags=re.I):
                    self.write_channel(self.password + self.TELNET_RETURN)
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
                self.remote_conn.close()
                msg = "Login failed: {}".format(self.host)
                raise NetMikoAuthenticationException(msg)

        # Last try to see if we already logged in
        self.write_channel(self.TELNET_RETURN)
        time.sleep(0.5 * delay_factor)
        output = self.read_channel()
        return_msg += output
        if re.search(pri_prompt_terminator, output, flags=re.M) or re.search(
            alt_prompt_terminator, output, flags=re.M
        ):
            return return_msg

        msg = "Login failed: {}".format(self.host)
        self.remote_conn.close()
        raise NetMikoAuthenticationException(msg)

    def _try_session_preparation(self):
        """
        Try to perform session preperation.

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

    def session_preparation(self):
        """
        Prepare the session after the connection has been established

        This method handles some differences that occur between various devices
        early on in the session.

        In general, it should include:
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width()
        self.clear_buffer()
        """
        self._test_channel_read()
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width()

        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def _use_ssh_config(self, dict_arg):
        """
        Update SSH connection parameters based on contents of SSH config file.

        Args:
            dict_arg (dict): Dictionary of SSH connection parameters

        """
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

    def _connect_params_dict(self):
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
            "timeout": self.timeout,
            "auth_timeout": self.auth_timeout,
            "banner_timeout": self.banner_timeout,
        }

        # Check if using SSH 'config' file mainly for SSH proxy support
        if self.ssh_config_file:
            conn_dict = self._use_ssh_config(conn_dict)
        return conn_dict

    def _sanitize_output(
        self, output, strip_command=False, command_string=None, strip_prompt=False
    ):
        """
        Strip out command echo, trailing router prompt and ANSI escape codes.

        Args:
            output (str): Output from a remote network device
            strip_command (bool): strip command or not
            command_string (str): command sent
            strip_prompt (bool): strip prompt or not

        """
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        output = self.normalize_linefeeds(output)
        if strip_command and command_string:
            command_string = self.normalize_linefeeds(command_string)
            output = self.strip_command(command_string, output)
        if strip_prompt:
            output = self.strip_prompt(output)
        return output

    def establish_connection(self, width=None, height=None):
        """
        Establish SSH connection to the network device

        Timeout will generate a NetMikoTimeoutException
        Authentication failure will generate a NetMikoAuthenticationException

        width and height are needed for Fortinet paging setting.

        Args:
            width (int): Specified width of the VT100 terminal window
            height (int): Specified height of the VT100 terminal window

        """
        if self.protocol == "telnet":
            self.remote_conn = telnetlib.Telnet(
                self.host, port=self.port, timeout=self.timeout
            )
            self.telnet_login()
        elif self.protocol == "serial":
            self.remote_conn = serial.Serial(**self.serial_settings)
            self.serial_login()
        elif self.protocol == "ssh":
            ssh_connect_params = self._connect_params_dict()
            self.remote_conn_pre = self._build_ssh_client()

            # initiate SSH connection
            try:
                self.remote_conn_pre.connect(**ssh_connect_params)
            except socket.error:
                self.paramiko_cleanup()
                msg = "Connection to device timed-out: {device_type} {ip}:{port}".format(
                    device_type=self.device_type, ip=self.host, port=self.port
                )
                raise NetMikoTimeoutException(msg)
            except paramiko.ssh_exception.AuthenticationException as auth_err:
                self.paramiko_cleanup()
                msg = "Authentication failure: unable to connect {device_type} {ip}:{port}".format(
                    device_type=self.device_type, ip=self.host, port=self.port
                )
                msg += self.RETURN + text_type(auth_err)
                raise NetMikoAuthenticationException(msg)

            if self.verbose:
                print(
                    "SSH connection established to {}:{}".format(self.host, self.port)
                )

            # Use invoke_shell to establish an 'interactive session'
            if width and height:
                self.remote_conn = self.remote_conn_pre.invoke_shell(
                    term="vt100", width=width, height=height
                )
            else:
                self.remote_conn = self.remote_conn_pre.invoke_shell()

            self.remote_conn.settimeout(self.blocking_timeout)
            if self.keepalive:
                self.remote_conn.transport.set_keepalive(self.keepalive)
            self.special_login_handler()
            if self.verbose:
                print("Interactive SSH session established")
        return ""

    def _test_channel_read(self, count=40, pattern=""):
        """
        Try to read the channel (generally post login) verify you receive data back.

        Args:
            count (int): the number of times to check the channel for data
            pattern (str): Regular expression pattern used to determine end of channel read

        """

        def _increment_delay(main_delay, increment=1.1, maximum=8):
            """
            Increment sleep time to a maximum value.

            Args:
                main_delay (int): primary delay to increment from
                increment (int): increment value
                maximum (int): maximum delay

            """
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
            new_data += self._read_channel_timing()
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
            raise NetMikoTimeoutException("Timed out waiting for data")

    def _build_ssh_client(self):
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

    def select_delay_factor(self, delay_factor):
        """
        Set delay factor.

        Choose the greater of delay_factor or self.global_delay_factor (default).
        In fast_cli choose the lesser of delay_factor of self.global_delay_factor.

        Args:
            delay_factor (int): See __init__: global_delay_factor

        """
        if self.fast_cli:
            if delay_factor <= self.global_delay_factor:
                return delay_factor
            else:
                return self.global_delay_factor
        else:
            if delay_factor >= self.global_delay_factor:
                return delay_factor
            else:
                return self.global_delay_factor

    def special_login_handler(self, delay_factor=1):
        """
        Handler for devices like WLC, Extreme ERS that throw up characters prior to login.

        Args:
            delay_factor (int): delay factor

        """
        pass

    def disable_paging(self, command="terminal length 0", delay_factor=1):
        """
        Disable paging default to a Cisco CLI method.

        Args:
            command (str): Device command to disable pagination of output
            delay_factor (int): See __init__: global_delay_factor

        """
        delay_factor = self.select_delay_factor(delay_factor)
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        command = self.normalize_cmd(command)
        log.debug("In disable_paging")
        log.debug("Command: {0}".format(command))
        self.write_channel(command)
        output = self.read_until_prompt()
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        log.debug("{0}".format(output))
        log.debug("Exiting disable_paging")
        return output

    def set_terminal_width(self, command="", delay_factor=1):
        """
        Set terminal width.

        CLI terminals try to automatically adjust the line based on the width of the terminal.
        This causes the output to get distorted when accessed programmatically.

        Set terminal width to 511 which works on a broad set of devices.

        Args:
            command (str): Command string to send to the device
            delay_factor (int): See __init__: global_delay_factor

        """
        if not command:
            return ""
        delay_factor = self.select_delay_factor(delay_factor)
        command = self.normalize_cmd(command)
        self.write_channel(command)
        output = self.read_until_prompt()
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        return output

    def set_base_prompt(
        self, pri_prompt_terminator="#", alt_prompt_terminator=">", delay_factor=1
    ):
        """
        Sets self.base_prompt

        Used as delimiter for stripping of trailing prompt in output.

        Should be set to something that is general and applies in multiple contexts. For Cisco
        devices this will be set to router hostname (i.e. prompt without > or hash symbol).

        This will be set on entering user exec or privileged exec on Cisco, but not when
        entering/exiting config mode.

        Args:
            pri_prompt_terminator (str): Primary trailing delimiter for identifying a device prompt
            alt_prompt_terminator (str): Alternate trailing delimiter for identifying a device prompt
            delay_factor (int): See __init__: global_delay_factor

        """
        prompt = self.find_prompt(delay_factor=delay_factor)
        if not prompt[-1] in (pri_prompt_terminator, alt_prompt_terminator):
            raise ValueError("Router prompt not found: {0}".format(repr(prompt)))
        # Strip off trailing terminator
        self.base_prompt = prompt[:-1]
        return self.base_prompt

    def find_prompt(self, delay_factor=1):
        """
        Finds the current network device prompt, last line only.

        Args:
            delay_factor (int): See __init__: global_delay_factor

        """
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        self.write_channel(self.RETURN)
        time.sleep(delay_factor * 0.1)

        # Initial attempt to get prompt
        prompt = self.read_channel()
        if self.ansi_escape_codes:
            prompt = self.strip_ansi_escape_codes(prompt)

        # Check if the only thing you received was a newline
        count = 0
        prompt = prompt.strip()
        while count <= 10 and not prompt:
            prompt = self.read_channel().strip()
            if prompt:
                if self.ansi_escape_codes:
                    prompt = self.strip_ansi_escape_codes(prompt).strip()
            else:
                self.write_channel(self.RETURN)
                time.sleep(delay_factor * 0.1)
            count += 1

        # If multiple lines in the output take the last line
        prompt = self.normalize_linefeeds(prompt)
        prompt = prompt.split(self.RESPONSE_RETURN)[-1]
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Unable to find prompt: {}".format(prompt))
        time.sleep(delay_factor * 0.1)
        self.clear_buffer()
        return prompt

    def clear_buffer(self):
        """Read any data available in the channel."""
        self.read_channel()

    def send_command_timing(
        self,
        command_string,
        delay_factor=1,
        max_loops=150,
        strip_prompt=True,
        strip_command=True,
        normalize=True,
        use_textfsm=False,
        use_genie=False,
    ):
        """
        Execute command_string on the SSH channel using a delay-based mechanism.

        Generally used for show commands.

        Args:
            command_string (str): The command to be executed on the remote device.
            delay_factor (int): Multiplying factor used to adjust delays (default: 1).
            max_loops (int): Controls wait time in conjunction with delay_factor. Will default to be
                based upon self.timeout.
            strip_prompt(bool): Remove the trailing router prompt from the output (default: True).
            strip_command (bool) : Remove the echo of the command from the output (default: True).
            normalize (bool): Ensure the proper enter is sent at end of command (default: True).
            use_textfsm (bool): Process command output through TextFSM template (default: False).
            use_genie (bool): Process command output through PyATS/Genie parser (default: False).

        """
        output = ""
        delay_factor = self.select_delay_factor(delay_factor)
        self.clear_buffer()
        if normalize:
            command_string = self.normalize_cmd(command_string)

        self.write_channel(command_string)
        output = self._read_channel_timing(
            delay_factor=delay_factor, max_loops=max_loops
        )
        output = self._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )
        # If both TextFSM and Genie are set, try TextFSM then Genie
        for parser_flag, parser_func in (
            (use_textfsm, get_structured_data),
            (use_genie, get_structured_data_genie),
        ):
            if parser_flag:
                structured_output = parser_func(
                    output, platform=self.device_type, command=command_string.strip()
                )
                # If we have structured data; return it.
                if not isinstance(structured_output, string_types):
                    return structured_output
        return output

    def strip_prompt(self, a_string):
        """
        Strip the trailing router prompt from the output.

        Args:
            a_string (str): Returned string from device

        """
        response_list = a_string.split(self.RESPONSE_RETURN)
        last_line = response_list[-1]
        if self.base_prompt in last_line:
            return self.RESPONSE_RETURN.join(response_list[:-1])
        else:
            return a_string

    def _first_line_handler(self, data, search_pattern):
        """
        Filter repainted first lines.

        In certain situations the first line will get repainted which causes a false
        match on the terminating pattern -- Filter this out.

        returns a tuple of (data, first_line_processed)

        Where data is the original data potentially with the first line modified
        and the first_line_processed is a flag indicating that we have handled the
        first line.

        Args:
            data (str): original string to search
            search_pattern (str): pattern to search for

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
        use_genie=False,
    ):
        """
        Execute command_string on the SSH channel using a pattern-based mechanism.

        Generally used for show commands. By default this method will keep waiting to receive data
        until the network device prompt is detected. The current network device prompt will be
        determined automatically.

        Args:
            command_string (str): The command to be executed on the remote device.
            expect_string (str): Regular expression pattern to use for determining end of output.
                If left blank will default to being based on router prompt.
            delay_factor (int): Multiplying factor used to adjust delays (default: 1).
            max_loops (int): Controls wait time in conjunction with delay_factor. Will default to be
                based upon self.timeout.
            auto_find_prompt (bool): try to find prompt automatically
            strip_prompt (bool): Remove the trailing router prompt from the output (default: True).
            strip_command (bool): Remove the echo of the command from the output (default: True).
            normalize (bool): Ensure the proper enter is sent at end of command (default: True).
            use_textfsm (bool): Process command output through TextFSM template (default: False).
            use_genie (bool): Process command output through PyATS/Genie parser (default: False).

        """
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

        i = 1
        output = ""
        past_three_reads = deque(maxlen=3)
        first_line_processed = False

        # Keep reading data until search_pattern is found or until max_loops is reached.
        while i <= max_loops:
            new_data = self.read_channel()
            if new_data:
                if self.ansi_escape_codes:
                    new_data = self.strip_ansi_escape_codes(new_data)

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
        else:  # nobreak
            raise IOError(
                "Search pattern never detected in send_command_expect: {}".format(
                    search_pattern
                )
            )

        output = self._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )

        # If both TextFSM and Genie are set, try TextFSM then Genie
        for parser_flag, parser_func in (
            (use_textfsm, get_structured_data),
            (use_genie, get_structured_data_genie),
        ):
            if parser_flag:
                structured_output = parser_func(
                    output, platform=self.device_type, command=command_string.strip()
                )
                # If we have structured data; return it.
                if not isinstance(structured_output, string_types):
                    return structured_output
        return output

    def send_command_expect(self, *args, **kwargs):
        """
        Support previous name of send_command method.

        Args:
            *args: Positional arguments to send to send_command()
            **kwargs: Keyword arguments to send to send_command()

        """
        return self.send_command(*args, **kwargs)

    @staticmethod
    def strip_backspaces(output):
        """
        Strip any backspace characters out of the output.

        Args:
            output (str): Output obtained from a remote network device.

        """
        backspace_char = "\x08"
        return output.replace(backspace_char, "")

    def strip_command(self, command_string, output):
        """
        Strip command_string from output string

        Cisco IOS adds backspaces into output for long commands (i.e. for commands that line wrap)

        Args:
            command_string (str): The command string sent to the device
            output (str): The returned output as a result of the command string sent to the device

        """
        backspace_char = "\x08"

        # Check for line wrap (remove backspaces)
        if backspace_char in output:
            output = output.replace(backspace_char, "")
            output_lines = output.split(self.RESPONSE_RETURN)
            new_output = output_lines[1:]
            return self.RESPONSE_RETURN.join(new_output)
        else:
            command_length = len(command_string)
            return output[command_length:]

    def normalize_linefeeds(self, a_string):
        r"""
        Convert `\r\r\n`,`\r\n`, `\n\r` to `\n.`

        Args:
            a_string (str): A string that may have non-normalized line feeds
                i.e. output returned from device, or a device prompt

        """
        newline = re.compile("(\r\r\r\n|\r\r\n|\r\n|\n\r)")
        a_string = newline.sub(self.RESPONSE_RETURN, a_string)
        if self.RESPONSE_RETURN == "\n":
            # Convert any remaining \r to \n
            return re.sub("\r", self.RESPONSE_RETURN, a_string)
        else:
            return a_string

    def normalize_cmd(self, command):
        """
        Normalize CLI commands to have a single trailing newline.

        Args:
            command (str): Command that may require line feed to be normalized

        """
        command = command.rstrip()
        command += self.RETURN
        return command

    def check_enable_mode(self, check_string=""):
        """
        Check if in enable mode. Return boolean.

        Args:
            check_string (str): Identification of privilege mode from device

        """
        self.write_channel(self.RETURN)
        output = self.read_until_prompt()
        return check_string in output

    def enable(self, cmd="", pattern="ssword", re_flags=re.IGNORECASE):
        """
        Enter enable mode.

        Args:
            cmd (str): Device command to enter enable mode
            pattern (str): pattern to search for indicating device is waiting for password
            re_flags (int): Regular expression flags used in conjunction with pattern

        """
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
            except NetMikoTimeoutException:
                raise ValueError(msg)
            if not self.check_enable_mode():
                raise ValueError(msg)
        return output

    def exit_enable_mode(self, exit_command=""):
        """
        Exit enable mode.

        Args:
            exit_command (str): Command that exits the session from privileged mode

        """
        output = ""
        if self.check_enable_mode():
            self.write_channel(self.normalize_cmd(exit_command))
            output += self.read_until_prompt()
            if self.check_enable_mode():
                raise ValueError("Failed to exit enable mode.")
        return output

    def check_config_mode(self, check_string="", pattern=""):
        """
        Checks if the device is in configuration mode or not.

        Args:
            check_string (str): Identification of configuration mode from the device
            pattern (str): Pattern to terminate reading of channel

        """
        self.write_channel(self.RETURN)
        # You can encounter an issue here (on router name changes) prefer delay-based solution
        if not pattern:
            output = self._read_channel_timing()
        else:
            output = self.read_until_pattern(pattern=pattern)
        return check_string in output

    def config_mode(self, config_command="", pattern=""):
        """
        Enter into config_mode.

        Args:
            config_command (str): Configuration command to send to the device
            pattern (str): Pattern to terminate reading of channel

        """
        output = ""
        if not self.check_config_mode():
            self.write_channel(self.normalize_cmd(config_command))
            output = self.read_until_pattern(pattern=pattern)
            if not self.check_config_mode():
                raise ValueError("Failed to enter configuration mode.")
        return output

    def exit_config_mode(self, exit_config="", pattern=""):
        """
        Exit from configuration mode.

        Args:
            exit_config (str): Command to exit configuration mode
            pattern (str): Pattern to terminate reading of channel

        """
        output = ""
        if self.check_config_mode():
            self.write_channel(self.normalize_cmd(exit_config))
            output = self.read_until_pattern(pattern=pattern)
            if self.check_config_mode():
                raise ValueError("Failed to exit configuration mode")
        log.debug("exit_config_mode: {}".format(output))
        return output

    def send_config_from_file(self, config_file=None, **kwargs):
        """
        Send configuration commands down the SSH channel from a file.

        The file is processed line-by-line and each command is sent down the
        SSH channel.

        **kwargs are passed to send_config_set method.

        Args:
            config_file (str): Path to configuration file to be sent to the device
            **kwargs (dict): params to be sent to send_config_set method

        """
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
    ):
        """
        Send configuration commands down the SSH channel.

        config_commands is an iterable containing all of the configuration commands.
        The commands will be executed one after the other.

        Automatically exits/enters configuration mode.

        Args:
            config_commands (list or string): Multiple configuration commands to be sent
            exit_config_mode (bool): Determines whether or not to exit config mode after complete
            delay_factor (int): Factor to adjust delays
            max_loops (int): Controls wait time in conjunction with delay_factor (default: 150)
            strip_prompt (bool): Determines whether or not to strip the prompt
            strip_command (bool): Determines whether or not to strip the command
            config_mode_command (str): The command to enter into config mode

        """
        delay_factor = self.select_delay_factor(delay_factor)
        if config_commands is None:
            return ""
        elif isinstance(config_commands, string_types):
            config_commands = (config_commands,)

        if not hasattr(config_commands, "__iter__"):
            raise ValueError("Invalid argument passed into send_config_set")

        # Send config commands
        cfg_mode_args = (config_mode_command,) if config_mode_command else tuple()
        output = self.config_mode(*cfg_mode_args)
        for cmd in config_commands:
            self.write_channel(self.normalize_cmd(cmd))
            if self.fast_cli:
                pass
            else:
                time.sleep(delay_factor * 0.05)

        # Gather output
        output += self._read_channel_timing(
            delay_factor=delay_factor, max_loops=max_loops
        )
        if exit_config_mode:
            output += self.exit_config_mode()
        output = self._sanitize_output(output)
        log.debug("{}".format(output))
        return output

    def strip_ansi_escape_codes(self, string_buffer):
        r"""
        Remove any ANSI (VT100) ESC codes from the output

        http://en.wikipedia.org/wiki/ANSI_escape_code

        Note: this does not capture ALL possible ANSI Escape Codes only the ones
        I have encountered

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
        ESC[00;32m   Color Green (30 to 37 are different colors) more general pattern is
                     ESC[\d\d;\d\dm and ESC[\d\d;\d\d;\d\dm
        ESC[6n       Get cursor position

        HP ProCurve and Cisco SG300 require this (possible others).

        Args:
            string_buffer (str): The string to be processed to remove ANSI escape codes

        """
        log.debug("In strip_ansi_escape_codes")
        log.debug("repr = {}".format(repr(string_buffer)))

        code_position_cursor = chr(27) + r"\[\d+;\d+H"
        code_show_cursor = chr(27) + r"\[\?25h"
        code_next_line = chr(27) + r"E"
        code_erase_line_end = chr(27) + r"\[K"
        code_erase_line = chr(27) + r"\[2K"
        code_erase_start_line = chr(27) + r"\[K"
        code_enable_scroll = chr(27) + r"\[\d+;\d+r"
        code_form_feed = chr(27) + r"\[1L"
        code_carriage_return = chr(27) + r"\[1M"
        code_disable_line_wrapping = chr(27) + r"\[\?7l"
        code_reset_mode_screen_options = chr(27) + r"\[\?\d+l"
        code_reset_graphics_mode = chr(27) + r"\[00m"
        code_erase_display = chr(27) + r"\[2J"
        code_graphics_mode = chr(27) + r"\[\d\d;\d\dm"
        code_graphics_mode2 = chr(27) + r"\[\d\d;\d\d;\d\dm"
        code_graphics_mode3 = chr(27) + r"\[(3|4)\dm"
        code_graphics_mode4 = chr(27) + r"\[(9|10)[0-7]m"
        code_get_cursor_position = chr(27) + r"\[6n"
        code_cursor_position = chr(27) + r"\[m"
        code_erase_display = chr(27) + r"\[J"
        code_attrs_off = chr(27) + r"\[0m"
        code_reverse = chr(27) + r"\[7m"

        code_set = [
            code_position_cursor,
            code_show_cursor,
            code_erase_line,
            code_enable_scroll,
            code_erase_start_line,
            code_form_feed,
            code_carriage_return,
            code_disable_line_wrapping,
            code_erase_line_end,
            code_reset_mode_screen_options,
            code_reset_graphics_mode,
            code_erase_display,
            code_graphics_mode,
            code_graphics_mode2,
            code_graphics_mode3,
            code_graphics_mode4,
            code_get_cursor_position,
            code_cursor_position,
            code_erase_display,
            code_attrs_off,
            code_reverse,
        ]

        output = string_buffer
        for ansi_esc_code in code_set:
            output = re.sub(ansi_esc_code, "", output)

        # CODE_NEXT_LINE must substitute with return
        output = re.sub(code_next_line, self.RETURN, output)

        log.debug("new_output = {0}".format(output))
        log.debug("repr = {0}".format(repr(output)))

        return output

    def cleanup(self):
        """Any needed cleanup before closing connection."""
        pass

    def paramiko_cleanup(self):
        """Cleanup Paramiko to try to gracefully handle SSH session ending."""
        self.remote_conn_pre.close()
        del self.remote_conn_pre

    def disconnect(self):
        """Try to gracefully close the SSH connection."""
        try:
            self.cleanup()
            if self.protocol == "ssh":
                self.paramiko_cleanup()
            elif self.protocol == "telnet":
                self.remote_conn.close()
            elif self.protocol == "serial":
                self.remote_conn.close()
        except Exception:
            # There have been race conditions observed on disconnect.
            pass
        finally:
            self.remote_conn_pre = None
            self.remote_conn = None
            self.close_session_log()

    def commit(self):
        """Commit method for platforms that support this."""
        raise AttributeError("Network device does not support 'commit()' method")

    def save_config(self, *args, **kwargs):
        """
        Not Implemented

        Args:
            *args: positional args
            **kwargs: keyword args

        """
        raise NotImplementedError

    def open_session_log(self, filename, mode="write"):
        """
        Open the session_log file.

        Args:
            filename (str): name of file to write to
            mode (str): write or append

        """
        if mode == "append":
            self.session_log = open(filename, mode="ab")
        else:
            self.session_log = open(filename, mode="wb")
        self._session_log_close = True

    def close_session_log(self):
        """Close the session_log file (if it is a file that we opened)."""
        if self.session_log is not None and self._session_log_close:
            self.session_log.close()
            self.session_log = None


class TelnetConnection(BaseConnection):
    pass
