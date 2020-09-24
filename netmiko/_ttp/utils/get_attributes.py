import re
import ast
import sys, traceback

import logging

log = logging.getLogger(__name__)


class _UndefSubst(dict):
    # class that overrides dictionary missing method to return value instead
    # of raising KeyError, that will lead to eval 'NameError: name ... is not defined',
    # that is needed to support simpler syntax definition, e.g. func_name="bla, name=value"
    # instead of func_name="'bla', name='value'"
    def __missing__(self, key):
        if key.lower() == "false":
            return False
        elif key.lower() == "true":
            return True
        elif key.lower() == "none":
            return None
        else:
            return key


def _get_args_kwargs(*args, **kwargs):
    # function to load args and kwargs
    return {"args": args, "kwargs": kwargs}


def get_attributes(line):
    """Extract attributes from variable line string.
    Example:
        'exclude(-VM-)' -> [{'name': 'exclude', 'args': ['-VM-'], 'kwargs': {}}]
    Args:
        line (str): string that contains variable attributes i.e. "contains('vlan') | upper | split('.')"
    Returns:
        List of opts dictionaries containing extracted attributes
    """

    result = []
    ATTRIBUTES = [i.strip() for i in line.split("|") if i.strip()]
    for item in ATTRIBUTES:
        opts = {"args": [], "kwargs": {}, "name": ""}
        # re search attributes like set(), upper, joinchar(',','-')
        try:
            itemDict = re.search(
                r"^(?P<name>\S+?)\s?(\((?P<options>.*)\))?$", item
            ).groupdict()
        except AttributeError as e:
            log.critical(
                "ttp.get_attributes failed to parse attributes for: '{}' with error: {};\nExiting...".format(
                    item, e
                )
            )
            raise SystemExit()
        opts["name"] = itemDict["name"]
        options = itemDict["options"]
        # create options list from options string using eval:
        if options:
            try:
                args_kwargs = eval(
                    "_get_args_kwargs({})".format(options), _UndefSubst(globals())
                )
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback_error = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )
                log.critical(
                    """Failed to load arg/kwargs from line '{}' for options '{}', traceback:\n{}""".format(
                        line, options, traceback_error
                    )
                )
                raise SystemExit()
            opts.update(args_kwargs)
        result.append(opts)
    return result