from typing import Any, Optional
from abc import ABC, abstractmethod
import codecs

import paramiko
import serial

from netmiko._telnetlib import telnetlib
from netmiko.utilities import write_bytes
from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.exceptions import ReadException, WriteException


class Channel(ABC):
    _stream_decoder: Optional[codecs.IncrementalDecoder] = None
    _stream_decoder_encoding: Optional[str] = None
    _stream_decoder_conn: Any = None

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

    def _decode_stream(self, data: bytes) -> str:
        """Decode newly received bytes as part of a continuous byte stream.

        A multi-byte character can be split across two reads; decoding each
        read independently with errors="ignore" silently drops the partial
        character, and the remaining bytes can even be reinterpreted as a
        different character (GH #3915). An incremental decoder buffers an
        incomplete trailing character until the rest of it arrives.

        The decoder is tied to the channel's current encoding and underlying
        connection: it is recreated if either changes, so bytes buffered from
        one connection can never leak into the decoded output of another.
        Incomplete bytes buffered under the old encoding are dropped in that
        case, matching the previous behavior of independent per-read decoding.
        Incomplete bytes still buffered when the stream ends are never
        emitted, matching the previous behavior (errors="ignore") for the
        byte-oriented encodings used with Netmiko (UTF-8, ASCII, Latin-1,
        GBK and similar).
        """
        encoding: str = self.encoding  # type: ignore[attr-defined]
        # Every concrete channel sets remote_conn in its __init__; the read
        # paths guard on it before reaching this helper.
        remote_conn: Any = self.remote_conn  # type: ignore[attr-defined]
        if (
            self._stream_decoder is None
            or self._stream_decoder_encoding != encoding
            or self._stream_decoder_conn is not remote_conn
        ):
            self._stream_decoder = codecs.getincrementaldecoder(encoding)(errors="ignore")
            self._stream_decoder_encoding = encoding
            self._stream_decoder_conn = remote_conn
        return self._stream_decoder.decode(data)

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
    def __init__(self, conn: Optional[paramiko.Channel], encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException("Attempt to write data, but there is no active channel.")
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
            output += self._decode_stream(outbuf)
        return output

    def read_channel(self) -> str:
        """Read all of the available data from the channel."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        output = ""
        while True:
            new_output = self.read_buffer()
            output += new_output
            # Loop on data availability rather than on the decoded output:
            # a chunk that ends mid-character yields no decodable text yet,
            # but the rest of the character may already be available.
            if not self.remote_conn.recv_ready():
                break
        return output


class TelnetChannel(Channel):
    def __init__(self, conn: Optional[telnetlib.Telnet], encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException("Attempt to write data, but there is no active channel.")
        self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))  # type: ignore

    def read_buffer(self) -> str:
        """Single read of available data."""
        raise NotImplementedError

    def read_channel(self) -> str:
        """Read all of the available data from the channel.

        This recreates telnetlib's read_very_eager() behavior ("drain everything
        currently available, without blocking") but as an O(n) operation.

        read_very_eager() accumulates cooked data into a single immutable bytes
        buffer (cookedq) that it re-copies on every loop iteration, which is
        O(n^2) for large reads (see netmiko GH #3872). Instead we loop the
        public read_eager() primitive, which drains cookedq on every call, and
        accumulate its results in a Python list, joining once at the end. Each
        concat therefore stays O(chunk) and the whole read is O(n).

        read_eager() returns as soon as it has any cooked data, so looping it
        until it yields nothing reproduces read_very_eager()'s greedy draining.
        The EOFError contract (raised on a closed connection with no buffered
        data, and relied on by telnet_login) is preserved: it is re-raised only
        when no data was collected.
        """
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")

        parts: list[bytes] = []
        while True:
            try:
                chunk = self.remote_conn.read_eager()  # type: ignore
            except EOFError:
                # Preserve read_very_eager()'s contract: only surface EOF when
                # there is no data to return.
                if not parts:
                    raise
                break
            if not chunk:
                break
            parts.append(chunk)
        return self._decode_stream(b"".join(parts))


class SerialChannel(Channel):
    def __init__(self, conn: Optional[serial.Serial], encoding: str) -> None:
        """
        Placeholder __init__ method so that reading and writing can be moved to the
        channel class.
        """
        self.remote_conn = conn
        # FIX: move encoding to GlobalState object?
        self.encoding = encoding

    def write_channel(self, out_data: str) -> None:
        if self.remote_conn is None:
            raise WriteException("Attempt to write data, but there is no active channel.")
        self.remote_conn.write(write_bytes(out_data, encoding=self.encoding))
        self.remote_conn.flush()

    def read_buffer(self) -> str:
        """Single read of available data."""
        if self.remote_conn is None:
            raise ReadException("Attempt to read, but there is no active channel.")
        if self.remote_conn.in_waiting > 0:
            output = self._decode_stream(self.remote_conn.read(self.remote_conn.in_waiting))
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
