from typing import Any, Optional, Union
from abc import ABC, abstractmethod
import paramiko
import telnetlib
import serial

from netmiko.utilities import write_bytes
from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.exceptions import ReadException, WriteException


class Channel(ABC):
    
    def __init__(self, conn: Union[paramiko.Channel, telnetlib.Telnet, serial.Serial], encoding: str) -> None:
        """Create the object."""
        self.remote_conn = conn
        self.encoding = encoding
        
    @abstractmethod
    def read_buffer(self) -> str:
        """Single read of available data."""
        return NotImplementedError

    @abstractmethod
    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        return NotImplementedError

    @abstractmethod
    def write_channel(self, out_data: str) -> None:
        """Write data down the channel."""
        return NotImplementedError


class SSHChannel(Channel):

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException(
                "Attempt to write data, but there is no active channel."
            )
        self.remote_conn.sendall(write_bytes(out_data, encoding=self.encoding))

    def read_buffer(self) -> str:
        """Single read of available data."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        output = ""
        if self.remote_conn.recv_ready():
            outbuf = self.remote_conn.recv(MAX_BUFFER)
            if len(outbuf) == 0:
                raise ReadException("Channel stream closed by remote device.")
            output += outbuf.decode(self.encoding, "ignore")
        return output

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        output = ""
        while True:
            new_output = self.read_buffer()
            output += new_output
            if new_output == "":
                break
        return output


class TelnetChannel(Channel):

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException(
                "Attempt to write data, but there is no active channel."
            )
        self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))

    def read_buffer(self) -> str:
        """Single read of available data."""
        raise NotImplementedError

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        return self.remote_conn.read_very_eager().decode(self.encoding, "ignore")


class SerialChannel(Channel):

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException(
                "Attempt to write data, but there is no active channel."
            )
        self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))
        self.remote_conn.flush()

    def read_buffer(self) -> str:
        """Single read of available data."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        if self.remote_conn.in_waiting > 0:
            output = self.remote_conn.read(self.remote_conn.in_waiting).decode(
                self.encoding, "ignore"
            )
            assert isinstance(output, str)
            return output
        else:
            return ""

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        output = ""
        while self.remote_conn.in_waiting > 0:
            output += self.read_buffer()
        return output
