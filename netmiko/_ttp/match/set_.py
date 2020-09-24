_name_map_ = {"set_func": "set"}


def set_func(data, value, match_line):
    vars = _ttp_["parser_object"].vars
    if data.rstrip() == match_line:
        if isinstance(value, str):
            if value in vars:
                return vars[value], None
            elif value in _ttp_["global_vars"]:
                return _ttp_["global_vars"][value], None
        return value, None
    else:
        return data, False