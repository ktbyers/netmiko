_name_map_ = {"csv_formatter": "csv"}


def csv_formatter(data, **kwargs):
    """Method to dump list of dictionaries into table
    using provided separator, default is comma - ','
    """
    result = ""
    # form table - list of lists
    table = _ttp_["formatters"]["table"](data, **kwargs)
    sep = kwargs.get("sep", ",")
    quote = kwargs.get("quote", '"')
    sep = "{q}{s}{q}".format(s=sep, q=quote)
    row_formatter = "\n{q}{{}}{q}".format(q=quote)
    # form results:
    result = "{q}{d}{q}".format(d=sep.join(table[0]), q=quote)
    for row in table[1:]:
        try:
            result += row_formatter.format(sep.join(row))
        except TypeError:  # might happen if not all values in row are strings
            result += row_formatter.format(sep.join([str(i) for i in row]))
    return result