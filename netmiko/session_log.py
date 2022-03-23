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
        no_log: Dict[str, Any] = None,
        record_writes: bool = False,
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
        if self.session_log and self._session_log_close:
            self.session_log.close()
            self.session_log = None

    def write(self, data: str) -> None:
        if self.session_log is not None and len(data) > 0:
            # Hide the password and secret in the session_log
            for hidden_data in self.no_log.values():
                data = data.replace(hidden_data, "********")

            if isinstance(self.session_log, io.BufferedIOBase):
                self.session_log.write(write_bytes(data, encoding=self.file_encoding))
            else:
                self.session_log.write(data)

            assert isinstance(self.session_log, io.BufferedIOBase) or isinstance(
                self.session_log, io.TextIOBase
            )
            self.session_log.flush()
