from typing import Any
from abc import ABC, abstractmethod

from netmiko.utilities import write_bytes
from netmiko.netmiko_globals import MAX_BUFFER


class Channel(ABC):
    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create the object."""
        pass

    # @abstractmethod
    # def __repr__(self) -> str:
    #     """String representation of the object."""
    #     pass
    #
    # @abstractmethod
    # def open(self, width: int = 511, height: int = 1000) -> None:
    #     """Create the underlying connection."""
    #     pass
    #
    # @abstractmethod
    # def close(self) -> None:
    #     """Close the underlying connection."""
    #     pass
    #
    # @abstractmethod
    # def login(self) -> None:
    #     """Handle the channel login process for any channel that requires it."""
    #     pass

    @abstractmethod
    def read_buffer(self) -> str:
        """Single read of available data. No sleeps."""
        pass

    @abstractmethod
    def read_channel(self) -> str:
        """Read all of the available data from the SSH channel. No sleeps."""
        pass

    @abstractmethod
    def write_channel(self, out_data: str) -> None:
        """Write data down the channel."""
        pass

    # @abstractmethod
    # def is_alive(self) -> bool:
    #     """Is the channel alive."""
    #     pass


class SSHChannel(Channel):
    def __init__(self, conn, encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is not None:
            self.remote_conn.sendall(write_bytes(out_data, encoding=self.encoding))

    def read_buffer(self) -> str:
        """Single read of available data."""
        output = ""
        if self.remote_conn is None:
            return output
        if self.remote_conn.recv_ready():
            outbuf = self.remote_conn.recv(MAX_BUFFER)
            if len(outbuf) == 0:
                raise EOFError("Channel stream closed by remote device.")
            output += outbuf.decode("utf-8", "ignore")
        return output

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        output = ""
        while True:
            new_output = self.read_buffer()
            output += new_output
            if new_output == "":
                break
        return output


class TelnetChannel(Channel):
    def __init__(self, conn, encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is not None:
            self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))

    def read_buffer(self) -> str:
        """Single read of available data."""
        raise NotImplementedError

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        return self.remote_conn.read_very_eager().decode("utf-8", "ignore")


class SerialChannel(Channel):
    def __init__(self, conn, encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is not None:
            self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))
            self.remote_conn.flush()

    def read_buffer(self) -> str:
        """Single read of available data."""
        if self.remote_conn.in_waiting > 0:
            return self.remote_conn.read(self.remote_conn.in_waiting).decode(
                "utf-8", "ignore"
            )

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        output = ""
        while self.remote_conn.in_waiting > 0:
            output += self.read_buffer()
        return output
