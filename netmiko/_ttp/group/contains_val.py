def contains_val(data, key, value):
    """
    check if certain key has certain value, return true if so and false otherwise
    """
    # try to get value variable from parser specific variables
    value = _ttp_["vars"].get(value, value)
    if not value in data.get(key, ""):
        return data, False
    return data, None