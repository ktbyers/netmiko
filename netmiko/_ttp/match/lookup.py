import logging

log = logging.getLogger(__name__)


def lookup(data, name=None, template=None, group=None, add_field=False):
    found_value = None
    lookup_data = {}
    # try get lookup dictionary/data from lookup tags:
    if name:
        path = [i.strip() for i in name.split(".")]
        lookup_data = _ttp_["parser_object"].lookups
    # get lookup data from template results
    elif template:
        path = [i.strip() for i in template.split(".")]
        for template in _ttp_["ttp_object"]._templates:
            if template.name == path[0]:
                # use first input results in the template:
                if isinstance(template.results, list):
                    lookup_data = template.results[0]
                # if not list its dictionary, per_template results mode used
                else:
                    lookup_data = template.results
                path = path[1:]
                break
    # get lookup data from group results
    elif group:
        path = [i.strip() for i in group.split(".")]
        for result in _ttp_["template_obj"].results:
            if path[0] in result:
                lookup_data = result[path[0]]
                break
        path = path[1:]
    else:
        log.info("ttp.lookup no lookup data name provided, doing nothing.")
        return data, None
    for i in path:
        lookup_data = lookup_data.get(i, {})
    # perform lookup:
    try:
        found_value = lookup_data[data]
    except KeyError:
        return data, None
    # decide to replace match result or add new field:
    if add_field is not False:
        return data, {"new_field": {add_field: found_value}}
    else:
        return found_value, None


def rlookup(data, name, add_field=False):
    path = [i.strip() for i in name.split(".")]
    found_value = None
    # get lookup dictionary/data:
    try:
        rlookup = _ttp_["parser_object"].lookups
        for i in path:
            rlookup = rlookup.get(i, {})
    except KeyError:
        return data, None
    # perfrom rlookup:
    if isinstance(rlookup, dict) is False:
        return data, None
    for key in rlookup.keys():
        if key in data:
            found_value = rlookup[key]
            break
    # decide to replace match result or add new field:
    if found_value is None:
        return data, None
    elif add_field is not False:
        return data, {"new_field": {add_field: found_value}}
    else:
        return found_value, None


def gpvlookup(data, name, add_field=False, record=False, multimatch=False):
    path = [i.strip() for i in name.split(".")]
    found_value = []
    # get lookup dictionary/data:
    try:
        lookup_data = _ttp_["parser_object"].lookups
        for i in path:
            lookup_data = lookup_data.get(i, {})
    except KeyError:
        log.error("gpvlookup: lookup data not found")
        return data, None
    # perform glob pattern values lookup
    if isinstance(lookup_data, dict) is False:
        log.error("gpvlookup: lookup data is not dictionary - {}".format())
        return data, None
    # import library
    from fnmatch import fnmatch

    # find first match and stop
    if multimatch is False:
        for key, patterns in lookup_data.items():
            for pattern in patterns:
                if fnmatch(data, pattern):
                    found_value.append(key)
                    break
            if found_value:
                break
    # iterate over all patterns and collect all matches
    elif multimatch is True:
        for key, patterns in lookup_data.items():
            found_value += [key for pattern in patterns if fnmatch(data, pattern)]
    # record found_value if told to do so:
    if record is not False:
        _ttp_["parser_object"].vars.update({record: found_value})
        _ttp_["global_vars"].update({record: found_value})
    # decide to replace match result or add new field:
    if not found_value:
        return data, None
    elif add_field is not False:
        return data, {"new_field": {add_field: found_value}}
    else:
        return found_value, None