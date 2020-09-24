def macro(data, macro_name):
    result = None
    if macro_name in _ttp_["macro"]:
        result = _ttp_["macro"][macro_name](data)
    # process macro result
    if result is None:
        return data
    return result