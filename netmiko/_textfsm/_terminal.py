"""
Google's clitable.py is inherently integrated to Linux.

This is a workaround for that (basically include modified clitable code without anything
that is Linux-specific).

_clitable.py is identical to Google's as of 2017-12-17
_texttable.py is identical to Google's as of 2017-12-17
_terminal.py is a highly stripped down version of Google's such that clitable.py works

https://github.com/google/textfsm/blob/master/clitable.py
"""

# Some of this code is from Google with the following license:
#
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re


__version__ = '0.1.1'


# ANSI, ISO/IEC 6429 escape sequences, SGR (Select Graphic Rendition) subset.
SGR = {
    'reset': 0,
    'bold': 1,
    'underline': 4,
    'blink': 5,
    'negative': 7,
    'underline_off': 24,
    'blink_off': 25,
    'positive': 27,
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37,
    'fg_reset': 39,
    'bg_black': 40,
    'bg_red': 41,
    'bg_green': 42,
    'bg_yellow': 43,
    'bg_blue': 44,
    'bg_magenta': 45,
    'bg_cyan': 46,
    'bg_white': 47,
    'bg_reset': 49,
    }

# Provide a familar descriptive word for some ansi sequences.
FG_COLOR_WORDS = {'black': ['black'],
                  'dark_gray': ['bold', 'black'],
                  'blue': ['blue'],
                  'light_blue': ['bold', 'blue'],
                  'green': ['green'],
                  'light_green': ['bold', 'green'],
                  'cyan': ['cyan'],
                  'light_cyan': ['bold', 'cyan'],
                  'red': ['red'],
                  'light_red': ['bold', 'red'],
                  'purple': ['magenta'],
                  'light_purple': ['bold', 'magenta'],
                  'brown': ['yellow'],
                  'yellow': ['bold', 'yellow'],
                  'light_gray': ['white'],
                  'white': ['bold', 'white']}

BG_COLOR_WORDS = {'black': ['bg_black'],
                  'red': ['bg_red'],
                  'green': ['bg_green'],
                  'yellow': ['bg_yellow'],
                  'dark_blue': ['bg_blue'],
                  'purple': ['bg_magenta'],
                  'light_blue': ['bg_cyan'],
                  'grey': ['bg_white']}


# Characters inserted at the start and end of ANSI strings
# to provide hinting for readline and other clients.
ANSI_START = '\001'
ANSI_END = '\002'


sgr_re = re.compile(r'(%s?\033\[\d+(?:;\d+)*m%s?)' % (
    ANSI_START, ANSI_END))


def StripAnsiText(text):
  """Strip ANSI/SGR escape sequences from text."""
  return sgr_re.sub('', text)
