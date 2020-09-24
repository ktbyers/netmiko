def sformat(data, string, add_field):
    """Function to format string with group match results.

    **Arguments**

    * data - match results data
    * string - string to format
    * add_field - name of the key to assign formatting results to
    """
    try:
        data[add_field] = string.format(**data)
    except KeyError:  # KeyError happens when not enough keys in **kwargs supplied to format method
        kwargs = _ttp_["global_vars"].copy()
        kwargs.update(_ttp_["vars"])
        kwargs.update(data)
        try:
            data[add_field] = string.format(**kwargs)
        except:
            pass
    return data, True