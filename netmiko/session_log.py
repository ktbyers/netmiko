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
            self.session_log = open(
                self.file_name, mode="a", encoding=self.file_encoding
            )
        else:
            self.session_log = open(
                self.file_name, mode="w", encoding=self.file_encoding
            )
        self._session_log_close = True

    def close(self) -> None:
        """Close the session_log file (if it is a file that we opened)."""
        self.flush()
        if self.session_log and self._session_log_close:
            self.session_log.close()
            self.session_log = None

    def no_log_filter(self, data: str) -> str:
        """Filter content from the session_log."""
        for hidden_data in self.no_log.values():
            data = data.replace(hidden_data, "********")
        return data

    def _read_buffer(self) -> str:
        self.slog_buffer.seek(0)
        data = self.slog_buffer.read()
        # Once read, create a new buffer
        self.slog_buffer = io.StringIO()
        return data

    def flush(self) -> None:
        """Force the slog_buffer to be written out to the actual file"""

        if self.session_log is not None:
            data = self._read_buffer()
            data = self.no_log_filter(data)

            if isinstance(self.session_log, io.BufferedIOBase):
                self.session_log.write(write_bytes(data, encoding=self.file_encoding))
            else:
                self.session_log.write(data)

            assert isinstance(self.session_log, io.BufferedIOBase) or isinstance(
                self.session_log, io.TextIOBase
            )

            # Flush the underlying file
            self.session_log.flush()

    def write(self, data: str) -> None:
        if len(data) > 0:
            self.slog_buffer.write(data)
