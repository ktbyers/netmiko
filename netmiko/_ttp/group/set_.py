_name_map_ = {"set_func": "set"}


def set_func(data, source, target="_use_source_", default="_no_default_value_"):
    # source - name of source variable to retrieve value
    # target - name of variable to save into
    if source in _ttp_["vars"]:
        source_var_value = _ttp_["vars"][source]
    elif default != "_no_default_value_":
        source_var_value = default
    else:
        source_var_value = source
    # get target var name:
    if target == "_use_source_":
        target = source
    data.update({target: source_var_value})
    return data, None