import logging

log = logging.getLogger(__name__)


def traverse(data, path):
    """Method to traverse dictionary data and return element
    at given path.
    """
    result = data
    # need to check path, in case of standalone function use
    if isinstance(path, str):
        path = [i.strip() for i in path.split(".")]
    if isinstance(data, dict):
        for i in path:
            result = result.get(i, {})
    elif isinstance(data, list):
        result = [traverse(i, path) for i in data]
    if result:
        return result
    else:
        return data


def _set_data(data, path, new_data):
    # not yet tested, hence not available
    # add new_data to data at given path or override existing results
    if isinstance(path, str):
        path = [i.strip() for i in path.split(".")]
    last_index = len(path) - 1
    datum = data
    for path_index, path_item in enumerate(path):
        if not isinstance(datum, dict):
            break
        if last_index == path_index:
            datum[path_item] = new_data
            break
        if path_item in datum:
            datum = datum[path_item]
        else:
            datum[path_item] = {}


def dict_to_list(data, key_name="key", path=None):
    """Flatten dictionary data, e.g. if data is this:
    { "Fa0"  : {"admin": "administratively down"},
      "Ge0/1": {"access_vlan": "24"}}
    and key_name="interface", it will become this list:
    [ {"admin": "administratively down", "interface": "Fa0"},
      {"access_vlan": "24", "interface": "Ge0/1"} ]
    """
    result = []
    if path:
        data = traverse(data, path)
    if isinstance(data, dict):
        for k, v in data.items():
            if not isinstance(v, dict):
                return data
            v.update({key_name: k})
            result.append(v)
    elif isinstance(data, list):
        # run recusrsion
        result = [dict_to_list(data=item, key_name=key_name) for item in data]
    return result