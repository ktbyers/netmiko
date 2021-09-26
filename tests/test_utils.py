#!/usr/bin/env python
"""
Implement common functions for tests
"""
import io
import sys
import functools

from datetime import datetime


def parse_yaml(yaml_file):
    """
    Parses a yaml file, returning its contents as a dict.
    """

    try:
        import yaml
    except ImportError:
        sys.exit("Unable to import yaml module.")

    try:
        with io.open(yaml_file, encoding="utf-8") as fname:
            return yaml.safe_load(fname)
    except IOError:
        sys.exit("Unable to open YAML file: {0}".format(yaml_file))


def f_exec_time(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        time_delta = end_time - start_time
        print(f"{str(func)}: Elapsed time: {time_delta}")
        return (time_delta, result)

    return wrapper_decorator
