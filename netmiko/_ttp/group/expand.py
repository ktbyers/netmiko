def expand(data):
    """
    Function to expand dot separated match variable names
    to nested dictionary structure
    """
    # do sanity check on data
    if not isinstance(data, dict):
        return data, True
    ret = {}
    # expand match variable names to dictionary
    for key, value in data.items():
        ref = ret
        keys = key.split("__dot_char__")
        while True:
            new_key = keys.pop(0)
            # handle last item in keys
            if not keys:
                if isinstance(ref, dict):
                    ref[new_key] = value
                break
            # expand dictionary tree
            ref = ref.setdefault(new_key, {})
    del data
    return ret, True