#!/usr/bin/env python
"""
Implement common functions for tests
"""

def parse_yaml(yaml_file):
    """
    Parses a yaml file, returning its contents as a dict.
    """

    try:
        import yaml
    except ImportError:
        print "Unable to import yaml module."

    try:
        with open(yaml_file) as fname:
            return yaml.load(fname)
    except IOError as (errno, strerr):
        print "I/O Error {0}: {1}".format(errno, strerr)
