def exclude_val(data, key, value):
    """
    check if certain key has certain value, return False if so and True otherwise
    """
    # try to get value variable from parser specific variables
    value = _ttp_["parser_object"].vars.get(value, value)
    try:
        if data[key] == value:
            return data, False
        else:
            return data, True
    except KeyError:
        return data, True