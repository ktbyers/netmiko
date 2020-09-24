def equal(data, key, value):
    """
    check if certain key has certain value, return true if so and false otherwise
    """
    # try to get value variable from parser specific variables
    value = _ttp_["vars"].get(value, value)
    if data.get(key) != value:
        return data, False
    return data, None