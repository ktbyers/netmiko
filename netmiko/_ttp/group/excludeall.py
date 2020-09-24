def excludeall(data, *args):
    # args = ('v4address', 'v4mask',)
    found_vars = []
    for var in args:
        if var in data:
            if var in _ttp_["results_object"].record["DEFAULTS"]:
                continue
            found_vars.append(var)
    if list(args) == found_vars:
        return data, False
    else:
        return data, True