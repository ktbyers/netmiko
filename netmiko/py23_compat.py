"""Simplify Python3 compatibility. Modeled after six behavior for small set of things"""
from __future__ import print_function
from __future__ import unicode_literals

import sys

PY2 = sys.version_info.major == 2
PY3 = sys.version_info.major == 3

if sys.version_info.major == 3:
    string_types = (str,)
    text_type = str
else:
    string_types = (basestring,)  # noqa
    text_type = unicode  # noqa
