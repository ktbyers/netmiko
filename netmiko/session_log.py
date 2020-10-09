import io
from netmiko.utilities import write_bytes


class SessionLog:
    def __init__(
        self,
        file_name=None,
        file_mode="write",
        file_encoding="ascii",
        record_writes=False,
        buffered_io=None,
    ):
        self.file_name = file_name
        self.file_mode = file_mode
        self.file_encoding = file_encoding
        self.record_writes = record_writes
        self._session_log_close = False

        # Actual file/file-handle/buffered-IO that will be written to.
        if file_name is None and buffered_io:
            self.session_log = buffered_io
        else:
            self.session_log = None

        # Ensures last write operations prior to disconnect are recorded.
        self.fin = False

    def open(self):
        """Open the session_log file."""
        if self.file_mode == "append":
            self.session_log = open(
                self.file_name, mode="a", encoding=self.file_encoding
            )
        else:
            self.session_log = open(
                self.file_name, mode="w", encoding=self.file_encoding
            )
        self._session_log_close = True

    def close(self):
        """Close the session_log file (if it is a file that we opened)."""
        if self.session_log and self._session_log_close:
            self.session_log.close()
            self.session_log = None

    def write(self, data):
        if self.session_log is not None and len(data) > 0:
            # Hide the password and secret in the session_log
            if self.password:
                data = data.replace(self.password, "********")
            if self.secret:
                data = data.replace(self.secret, "********")
            if isinstance(self.session_log, io.BufferedIOBase):
                data = self.normalize_linefeeds(data)
                self.session_log.write(write_bytes(data, encoding=self.file_encoding))
            else:
                self.session_log.write(self.normalize_linefeeds(data))
            self.session_log.flush()
