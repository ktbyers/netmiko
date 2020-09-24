def macro(data, macro_name):
    result = None
    if macro_name in _ttp_["macro"]:
        result = _ttp_["macro"][macro_name](data)
    # process macro result
    if result is True:
        return data, True
    elif result is False:
        return data, False
    elif result is None:
        return data, None
    elif isinstance(result, tuple):
        if len(result) == 2:
            if isinstance(result[1], dict):
                return result[0], {"new_field": result[1]}
    return result, None