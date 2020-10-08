class SessionLog:
    def __init__(self, file_name="", record_writes=False, file_mode="write", buffered_io=None):
        self.file_name = file_name
        self.record_writes = False
        self.file_mode = file_mode

1876     def open_session_log(self, filename, mode="write"):
1877         """Open the session_log file."""
1878         if mode == "append":
1879             self.session_log = open(filename, mode="a", encoding=self.encoding)
1880         else:
1881             self.session_log = open(filename, mode="w", encoding=self.encoding)
1882         self._session_log_close = True
1883 
1884     def close_session_log(self):
1885         """Close the session_log file (if it is a file that we opened)."""
1886         if self.session_log is not None and self._session_log_close:
1887             self.session_log.close()
1888             self.session_log = None

 427     def _write_session_log(self, data):
 428         if self.session_log is not None and len(data) > 0:
 429             # Hide the password and secret in the session_log
 430             if self.password:
 431                 data = data.replace(self.password, "********")
 432             if self.secret:
 433                 data = data.replace(self.secret, "********")
 434             if isinstance(self.session_log, io.BufferedIOBase):
 435                 data = self.normalize_linefeeds(data)
 436                 self.session_log.write(write_bytes(data, encoding=self.encoding))
 437             else:
 438                 self.session_log.write(self.normalize_linefeeds(data))
 439             self.session_log.flush()
