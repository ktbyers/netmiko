def table(data, **kwargs):
    """Method to form table there table is list of lists,
    first item - headers row. Method used by csv/tabulate/excel
    formatters.
    """
    table = []
    headers = set()
    data_to_table = []
    source_data = []
    # get attributes:
    provided_headers = kwargs.get("headers", None)
    path = kwargs.get("path", [])
    missing = kwargs.get("missing", "")
    key = kwargs.get("key", "")
    # normalize source_data to list:
    if isinstance(data, list):  # handle the case for template/global output
        source_data += data
    elif isinstance(data, dict):  # handle the case for group specific output
        source_data.append(data)
    # form data_to_table:
    for datum in source_data:
        item = _ttp_["output"]["traverse"](datum, path)
        if not item:  # skip empty results
            continue
        elif isinstance(item, list):
            data_to_table += item
        elif isinstance(item, dict):
            # flatten dictionary data if key was given
            if key:
                data_to_table += _ttp_["output"]["dict_to_list"](
                    data=item, key_name=key
                )
            else:
                data_to_table.append(item)
    # create headers:
    if provided_headers:
        headers = provided_headers
    else:
        # headers is a set, set.update only adds unique values to set
        [headers.update(list(item.keys())) for item in data_to_table]
        headers = sorted(list(headers))
    # save headers row in table:
    table.insert(0, headers)
    # fill in table with data:
    for item in data_to_table:
        row = [missing for _ in headers]
        for k, v in item.items():
            if k in headers:
                row[headers.index(k)] = v
        table.append(row)
    return table