import logging

log = logging.getLogger(__name__)


def to_str(data):
    return str(data), None


def to_list(data):
    return [data], None


def to_int(data):
    try:
        return int(data), None
    except ValueError:
        log.error(
            "ttp.to_int: ValueError, failed to convert value '{}' to integer".format(
                data
            )
        )
        return data, None


def to_float(data):
    try:
        return float(data), None
    except TypeError:
        log.error(
            "ttp.to_int: TypeError, failed to convert value '{}' to float".format(data)
        )
        return data, None


def to_unicode(data):
    if _ttp_["python_major_version"] == 2:
        try:
            return unicode(data), None
        except:
            log.error(
                "ttp.to_int: failed to convert value '{}' to unicode string".format(
                    data
                )
            )
    return data, None
