# -*- coding: utf-8 -*-
"""
This function took most of the code from 'parsetime' python library:
https://pypi.org/project/python-parsetime/

but code was stripped to provide matching for required time formats only
"""

import re

YEARS = r"(?P<years>\d+)\s*(?:ys?|yrs?.?|years?)"
MONTHS = r"(?P<months>\d+)\s*(?:mos?.?|mths?.?|months?)"
WEEKS = r"(?P<weeks>[\d.]+)\s*(?:w|wks?|weeks?)"
DAYS = r"(?P<days>[\d.]+)\s*(?:d|dys?|days?)"
HOURS = r"(?P<hours>[\d.]+)\s*(?:h|hrs?|hours?)"
MINS = r"(?P<mins>[\d.]+)\s*(?:m|(mins?)|(minutes?))"
SECS = r"(?P<secs>[\d.]+)\s*(?:s|secs?|seconds?)"
SEPARATORS = r"[,/]"

OPT = lambda x: r"(?:{x})?".format(x=x)
OPTSEP = lambda x: r"(?:{x}\s*(?:{SEPARATORS}\s*)?)?".format(x=x, SEPARATORS=SEPARATORS)

TIMEFORMATS = [
    r"{YEARS}\s*{MONTHS}\s*{WEEKS}\s*{DAYS}\s*{HOURS}\s*{MINS}\s*{SECS}".format(
        YEARS=OPTSEP(YEARS),
        MONTHS=OPTSEP(MONTHS),
        WEEKS=OPTSEP(WEEKS),
        DAYS=OPTSEP(DAYS),
        HOURS=OPTSEP(HOURS),
        MINS=OPTSEP(MINS),
        SECS=OPT(SECS),
    )
]

COMPILED_TIMEFORMATS = [
    re.compile(r"\s*" + timefmt + r"\s*$", re.I) for timefmt in TIMEFORMATS
]

MULTIPLIERS = dict(
    [
        ("years", 60 * 60 * 24 * 365),
        ("months", 60 * 60 * 24 * 30),
        ("weeks", 60 * 60 * 24 * 7),
        ("days", 60 * 60 * 24),
        ("hours", 60 * 60),
        ("mins", 60),
        ("secs", 1),
    ]
)


def uptimeparse(data, format="seconds"):
    """
    Parse a time expression like:
    2 years, 27 weeks, 3 days, 10 hours, 46 minutes
    27 weeks, 3 days, 10 hours, 48 minutes

    returning a number of seconds.
    """
    for timefmt in COMPILED_TIMEFORMATS:
        match = timefmt.match(data)
        if match and match.group(0).strip():
            mdict = match.groupdict()
            # if all of the fields are integer numbers
            if all(v.isdigit() for v in list(mdict.values()) if v):
                if format == "seconds":
                    return (
                        sum(
                            [
                                MULTIPLIERS[k] * int(v, 10)
                                for (k, v) in list(mdict.items())
                                if v is not None
                            ]
                        ),
                        None,
                    )
                elif format == "dict":
                    return {k: v for k, v in mdict.items() if v is not None}, None
                break
    return data, None