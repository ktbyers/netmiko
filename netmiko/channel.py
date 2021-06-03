from typing import Any, Callable, Optional
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
import functools

from netmiko import log
from netmiko.utilities import write_bytes
from netmiko.netmiko_globals import MAX_BUFFER

if TYPE_CHECKING:
    from netmiko.session_log import SessionLog


def log_writes(func: Callable[..., None]) -> Callable[..., None]:
    """Handle both session_log and log of writes."""

    @functools.wraps(func)
    def wrapper_decorator(self: "Channel", out_data: str) -> None:
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

    return wrapper_decorator


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
        """Single read of available data."""
        pass

    @abstractmethod
    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
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
    def __init__(
        self, conn, encoding: str, session_log: Optional["SessionLog"] = None
    ) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding
        self.session_log = session_log

    @log_writes
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
    def __init__(
        self, conn, encoding: str, session_log: Optional["SessionLog"] = None
    ) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding
        self.session_log = session_log

    @log_writes
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
    def __init__(
        self, conn, encoding: str, session_log: Optional["SessionLog"] = None
    ) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding
        self.session_log = session_log

    @log_writes
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
