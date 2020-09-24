from re import search


def extract_commands(data, *commands):
    """Input function to find commands output in the "data" text"""
    ret = ""
    hostname = _ttp_["variable"]["gethostname"](data, "input find_command function")
    if hostname:
        for command in commands:
            regex = r"{}[#>] *{} *\n([\S\s]+?)(?={}[#>]|$)".format(
                hostname, command, hostname
            )
            match = search(regex, data)
            if match:
                ret += "\n{}\n".format(match.group())
        if ret:
            return ret, None
    return data, None