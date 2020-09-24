_name_map_ = {"delete_func": "del"}


def delete_func(data, *args):
    for key in args:
        if key in data:
            _ = data.pop(key)
    return data, None