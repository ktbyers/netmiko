import io
from netmiko.utilities import write_bytes
from typing import Dict, Any, Union, Optional, TextIO


class SessionLog:
    def __init__(
        self,
        file_name: Optional[str] = None,
        buffered_io: Optional[io.BufferedIOBase] = None,
        file_mode: str = "write",
        file_encoding: str = "utf-8",
        no_log: Optional[Dict[str, Any]] = None,
        record_writes: bool = False,
        slog_buffer: Optional[io.StringIO] = None,
    ) -> None:
        if no_log is None:
            self.no_log = {}
        else:
            self.no_log = no_log
        self.file_name = file_name
        self.file_mode = file_mode
        self.file_encoding = file_encoding
        self.record_writes = record_writes
        self._session_log_close = False

        # Actual file/file-handle/buffered-IO that will be written to.
        self.session_log: Union[io.BufferedIOBase, TextIO, None]
        if file_name is None and buffered_io:
            self.session_log = buffered_io
        else:
            self.session_log = None

        # In order to ensure all the no_log entries get hidden properly,
        # we must first store everying in memory and then write out to file.
        # Otherwise, we might miss the data we are supposed to hide (since
        # the no_log data potentially spans multiple reads).
        if slog_buffer is None:
            self.slog_buffer = io.StringIO()

        # Ensures last write operations prior to disconnect are recorded.
        self.fin = False

    def open(self) -> None:
        """Open the session_log file."""
        if self.file_name is None:
            return None
        if self.file_mode == "append":
            self.session_log = open(self.file_name, mode="a", encoding=self.file_encoding)
        else:
            self.session_log = open(self.file_name, mode="w", encoding=self.file_encoding)
        self._session_log_close = True

    def close(self) -> None:
        """Close the session_log file (if it is a file that we opened)."""
        self._flush_buffer(final=True)
        if self.session_log and self._session_log_close:
            self.session_log.close()
            self.session_log = None

    def no_log_filter(self, data: str) -> str:
        """Filter content from the session_log."""
        for hidden_data in self.no_log.values():
            data = data.replace(hidden_data, "********")
        return data

    def _longest_partial_match(self, data: str) -> int:
        """Return the length of the longest suffix of data that is a partial
        prefix of any no_log value. Used to hold back data that might be the
        start of a secret split across multiple channel reads."""
        hold_back = 0
        for hidden_data in self.no_log.values():
            for partial_len in range(1, len(hidden_data)):
                if data.endswith(hidden_data[:partial_len]):
                    hold_back = max(hold_back, partial_len)
        return hold_back

    def _read_buffer(self) -> str:
        self.slog_buffer.seek(0)
        data = self.slog_buffer.read()
        # Once read, create a new buffer
        self.slog_buffer = io.StringIO()
        return data

    def _write(self, data: str) -> None:
        """Write data to the underlying IO sink and flush it."""
        assert self.session_log is not None
        if isinstance(self.session_log, io.BufferedIOBase):
            self.session_log.write(write_bytes(data, encoding=self.file_encoding))
        else:
            self.session_log.write(data)

        assert isinstance(self.session_log, io.BufferedIOBase) or isinstance(
            self.session_log, io.TextIOBase
        )

        self.session_log.flush()

    def _flush_buffer(self, final: bool = False) -> None:
        """Drain slog_buffer to the sink.

        If final=False (normal write path), any trailing data that is a partial
        prefix of a no_log value is held back in the buffer so the next write
        can complete the match before filtering.

        If final=True (close path), any held-back partial match is replaced
        with '********' rather than exposing a fragment of the secret.
        """
        if self.session_log is None:
            return

        data = self._read_buffer()

        if self.no_log and data:
            hold_back = self._longest_partial_match(data)
            if hold_back:
                if final:
                    data = data[:-hold_back] + "********"
                else:
                    self.slog_buffer.write(data[-hold_back:])
                    data = data[:-hold_back]
            data = self.no_log_filter(data)

        if data:
            self._write(data)

    def flush(self) -> None:
        """Force any buffered data to be written to the sink immediately."""
        self._flush_buffer()

    def write(self, data: str) -> None:
        if len(data) > 0:
            self.slog_buffer.write(data)
            self._flush_buffer()
