import logging

log = logging.getLogger(__name__)


def str_to_unicode(data):
    if _ttp_["python_major_version"] == 3:
        return data, None
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = unicode(value)
    return data, None


def to_int(data, *keys):
    if not keys:
        keys = list(data.keys())
    for k in keys:
        v = data[k]
        try:
            data[k] = int(v)
        except ValueError:
            try:
                data[k] = float(v)
            except:
                continue
    return data, None