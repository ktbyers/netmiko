def record(data, source, target="_use_source_"):
    if source in data:
        # get source var value:
        source_var_value = data[source]
        # get target var name:
        if target == "_use_source_":
            target = source
        # record variable:
        _ttp_["vars"].update({target: source_var_value})
        _ttp_["global_vars"].update({target: source_var_value})
    return data, None