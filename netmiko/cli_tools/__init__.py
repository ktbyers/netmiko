import os


__version__ = "5.0.0"
MAX_WORKERS = int(os.environ.get("NETMIKO_MAX_THREADS", 10))
ERROR_PATTERN = "%%%failed%%%"

GREP = "/bin/grep"
if not os.path.exists(GREP):
    GREP = "/usr/bin/grep"
