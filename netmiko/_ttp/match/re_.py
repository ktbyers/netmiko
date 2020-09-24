import re


def startswith_re(data, pattern):
    if re.search("^{}".format(pattern), data):
        return data, True
    return data, False


def endswith_re(data, pattern):
    if re.search("{}$".format(pattern), data):
        return data, True
    return data, False


def contains_re(data, pattern):
    if re.search(pattern, data):
        return data, True
    return data, False


def notstartswith_re(data, pattern):
    if not re.search("^{}".format(pattern), data):
        return data, True
    return data, False


def notendswith_re(data, pattern):
    if not re.search("{}$".format(pattern), data):
        return data, True
    return data, False


def exclude_re(data, pattern):
    if not re.search(pattern, data):
        return data, True
    return data, False


def resub(data, old, new, count=1):
    vars = _ttp_["parser_object"].vars
    if old in vars:
        return re.sub(re.escape(vars[old]), new, data, count=count), None
    return re.sub(old, new, data, count=count), None


def resuball(data, *args):
    vars = _ttp_["parser_object"].vars
    args = list(args)
    new = ""
    if len(args) > 1:
        new = args.pop(0)
    for oldValue in args:
        if oldValue in vars:
            if isinstance(vars[oldValue], list):
                for oldVal in vars[oldValue]:
                    if isinstance(oldVal, str):
                        data = re.sub(oldVal, new, data)
            elif isinstance(vars[oldValue], dict):
                for newVal, oldVal in vars[oldValue].items():
                    if isinstance(oldVal, list):
                        for i in oldVal:
                            if isinstance(i, str):
                                data = re.sub(i, newVal, data)
                    elif isinstance(oldVal, str):
                        data = re.sub(oldVal, newVal, data)
            elif isinstance(vars[oldValue], str):
                data = re.sub(re.escape(vars[oldValue]), new, data)
        else:
            data = re.sub(oldValue, new, data)
    return data, None