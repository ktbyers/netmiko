from os import path
import socket
import telnetlib
import paramiko
import serial

from netmiko import log
from netmiko.ssh_exception import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)
from netmiko.netmiko_globals import MAX_BUFFER


class Channel:
    def __init__(self, protocol):
        self.protocol = protocol
        self.remote_conn = None

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
        if self.ansi_escape_codes:
            output = self.strip_ansi_escape_codes(output)
        log.debug(f"read_channel: {output}")
        self._write_session_log(output)
        return output


class TelnetChannel(Channel):
    def __init__(self):
        self.protocol = "telnet"
        self.remote_conn = None

    def __repr__(self):
        return "TelnetChannel()"

    def establish_connection(self, width=511, height=1000):
        self.remote_conn = telnetlib.Telnet(
            self.host, port=self.port, timeout=self.timeout
        )
        # FIX - move telnet_login into this class
        self.telnet_login()


class SSHChannel(Channel):
    def __init__(self, ssh_params, ssh_hostkey_args=None):
        self.ssh_params = ssh_params
        if ssh_hostkey_args is None:
            self.ssh_hostkey_args = {}
        else:
            self.ssh_hostkey_args = ssh_hostkey_args
        self.protocol = "ssh"
        self.remote_conn = None

    def __repr__(self):
        return "SSHChannel(ssh_params)"

    def _build_ssh_client(self):
        """Prepare for Paramiko SSH connection."""
        # Create instance of SSHClient object
        remote_conn_pre = paramiko.SSHClient()

        # Load host_keys for better SSH security
        if self.ssh_hostkey_args.get("system_host_keys"):
            remote_conn_pre.load_system_host_keys()
        if self.ssh_hostkey_args.get("alt_host_keys"):
            alt_key_file = self.ssh_hostkey_args["alt_key_file"]
            if path.isfile(alt_key_file):
                remote_conn_pre.load_host_keys(alt_key_file)

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        if not self.ssh_hostkey_args.get("ssh_strict", False):
            key_policy = paramiko.AutoAddPolicy()
        else:
            key_policy = paramiko.RejectPolicy()

        remote_conn_pre.set_missing_host_key_policy(key_policy)
        return remote_conn_pre

    def establish_connection(self, width=511, height=1000):
        self.remote_conn_pre = self._build_ssh_client()

        # initiate SSH connection
        try:
            self.remote_conn_pre.connect(**self.ssh_params)
        except socket.error as conn_error:
            self.paramiko_cleanup()
            msg = f"""TCP connection to device failed.

on causes of this problem are:
ncorrect hostname or IP address.
rong TCP port.
ntermediate firewall blocking access.

ce settings: {self.device_type} {self.host}:{self.port}

"""

            # Handle DNS failures separately
            if "Name or service not known" in str(conn_error):
                msg = (
                    f"DNS failure--the hostname you provided was not resolvable "
                    f"in DNS: {self.host}:{self.port}"
                )

            msg = msg.lstrip()
            raise NetmikoTimeoutException(msg)
        except paramiko.ssh_exception.SSHException as no_session_err:
            self.paramiko_cleanup()
            if "No existing session" in str(no_session_err):
                msg = (
                    "Paramiko: 'No existing session' error: "
                    "try increasing 'conn_timeout' to 10 seconds or larger."
                )
                raise NetmikoTimeoutException(msg)
            else:
                raise
        except paramiko.ssh_exception.AuthenticationException as auth_err:
            self.paramiko_cleanup()
            msg = f"""Authentication to device failed.

on causes of this problem are:
nvalid username and password
ncorrect SSH-key file
onnecting to the wrong device

ce settings: {self.device_type} {self.host}:{self.port}

"""

            msg += self.RETURN + str(auth_err)
            raise NetmikoAuthenticationException(msg)

        if self.verbose:
            print(f"SSH connection established to {self.host}:{self.port}")

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre.invoke_shell(
            term="vt100", width=width, height=height
        )

        self.remote_conn.settimeout(self.blocking_timeout)
        if self.keepalive:
            self.remote_conn.transport.set_keepalive(self.keepalive)
        self.special_login_handler()
        if self.verbose:
            print("Interactive SSH session established")


class SerialChannel(Channel):
    def __init__(self):
        self.protocol = "serial"
        self.remote_conn = None

    def __repr__(self):
        return "SerialChannel()"

    def establish_connection(self, width=511, height=1000):
        self.remote_conn = serial.Serial(**self.serial_settings)
        self.serial_login()
