import logging

log = logging.getLogger(__name__)


def lookup(
    data,
    key,
    name=None,
    template=None,
    group=None,
    add_field=False,
    replace=True,
    update=False,
):
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
        # look for group that parses same input
        if path[0] in _ttp_["parser_object"].main_results:
            lookup_data = _ttp_["parser_object"].main_results[path[0]]
        # try to find results for group that parsed different input
        else:
            for result in _ttp_["template_obj"].results:
                if path[0] in result:
                    lookup_data = result[path[0]]
                    break
        path = path[1:]
    else:
        log.info("ttp.group.lookup no lookup data found, doing nothing.")
        return data, None
    # traverse to lookup data
    for i in path:
        lookup_data = lookup_data.get(i, {})
    # perform lookup:
    try:
        if isinstance(lookup_data, dict):
            found_value = lookup_data[data[key]]
    except KeyError:
        return data, None
    # decide what action to do with found value
    if add_field:
        try:
            data[add_field] = found_value
        except:
            log.error("ttp.group.lookup failed to add new field '{}'".format(add_field))
    elif update is True and isinstance(found_value, dict):
        data.update(found_value)
    elif replace:
        data[key] = found_value
    else:
        log.warning(
            "ttp.group.lookup nothing done, make sure action directives are correct"
        )
    return data, None
