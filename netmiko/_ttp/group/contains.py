def contains(data, *args):
    # args = ('v4address', 'v4mask',)
    for var in args:
        if var in data:
            if var in _ttp_["results_object"].record["DEFAULTS"]:
                if _ttp_["results_object"].record["DEFAULTS"][var] == data[var]:
                    return data, False
            return data, True
    return data, False