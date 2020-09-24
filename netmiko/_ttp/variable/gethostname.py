# -*- coding: utf-8 -*-

from re import finditer
import logging

log = logging.getLogger(__name__)


def gethostname(data, *args, **kwargs):
    """Description: Method to find hostname in show
    command output, uses symbols '# ', '<', '>' to find hostname
    """
    REs = [  # ios-xr prompt re must go before ios privilege prompt re
        {"ios_xr": r"\n\S+:(\S+)#.*(?=\n)"},  # e.g. 'RP/0/4/CPU0:hostname#'
        {"ios_priv": r"\n(\S+)#.*(?=\n)"},  # e.g. 'hostname#'
        {"juniper": r"\n\S*@(\S+)>.*(?=\n)"},  # e.g. 'some.user@router-fw-host>'
        {"huawei": r"\n<(\S+)>.*(?=\n)"},  # e.g. '<hostname>'
        {"ios_exec": r"\n(\S+)>.*(?=\n)"},  # e.g. 'hostname>'
        {
            "fortigate": r"\n(\S+ \(\S+\)) #.*(?=\n)"
        },  # e.g. 'forti-hostname (Default) #'
    ]
    UTF_BOM = [
        "ï»¿",
        "þÿ",
        "ÿþ",
        "\ufeff",
    ]  # byte order marks (BOM) to strip from beginning
    # of the hostname, some text files can have them
    for item in REs:
        name, regex = list(item.items())[0]
        match_iter = finditer(regex, data)
        try:
            match = next(match_iter)
            hostname_match = match.group(1)
            for i in UTF_BOM:
                hostname_match = hostname_match.lstrip(i)
            return hostname_match
        except StopIteration:
            continue
    log.error(
        'ttp.functions.variable_gethostname: "{}" file, Hostname not found'.format(
            args[0]
        )
    )
    return False