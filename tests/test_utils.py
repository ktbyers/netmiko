#!/usr/bin/env python
"""
Implement common functions for tests
"""
from __future__ import print_function
from __future__ import unicode_literals

import io
import sys

def parse_yaml(yaml_file):
    """
    Parses a yaml file, returning its contents as a dict.
    """

    try:
        import yaml
    except ImportError:
        sys.exit("Unable to import yaml module.")

    try:
        with io.open(yaml_file, encoding='utf-8') as fname:
            return yaml.load(fname)
    except IOError:
        sys.exit("Unable to open YAML file: {0}".format(yaml_file))
