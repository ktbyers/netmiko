"""Simplify Python3 compatibility. Modeled after six behavior for small set of things"""
from __future__ import print_function
from __future__ import unicode_literals

import io
import sys

PY2 = sys.version_info.major == 2
PY3 = sys.version_info.major == 3

if PY3:
    string_types = (str,)
    text_type = str
    bufferedio_types = io.BufferedIOBase
else:
    string_types = (basestring,)  # noqa
    text_type = unicode  # noqa
    bufferedio_types = (io.BufferedIOBase, file)    # noqa
