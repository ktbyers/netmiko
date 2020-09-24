def macro(data, *macro):
    result = "_not_changed_"
    # extract macro names
    macro_names_list = []
    for item in macro:
        macro_names_list += (
            [i.strip() for i in item.split(",")] if "," in item else [item]
        )
    # run macro
    for macro_item in macro_names_list:
        if macro_item in _ttp_["macro"]:
            result = _ttp_["macro"][macro_item](data)
    # process macro result
    if result is True:
        return data, True
    elif result is False:
        return data, False
    elif result == "_not_changed_":
        return data, None
    return result, None