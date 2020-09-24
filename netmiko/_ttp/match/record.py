def record(data, record):
    _ttp_["parser_object"].vars.update({record: data})
    _ttp_["global_vars"].update({record: data})
    return data, None