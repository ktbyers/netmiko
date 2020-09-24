def count(data, var=None, globvar=None):
    if var:
        try:
            _ttp_["parser_object"].vars[var] += 1
        except KeyError:
            _ttp_["parser_object"].vars[var] = 1

    if globvar:
        try:
            _ttp_["global_vars"][globvar] += 1
        except KeyError:
            _ttp_["global_vars"][globvar] = 1

    return data, None