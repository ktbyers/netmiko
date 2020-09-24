PHRASE = r"(\S+ {1})+?\S+"
ROW = r"(\S+ +)+?\S+"
ORPHRASE = r"\S+|(\S+ {1})+?\S+"
DIGIT = r"\d+"
IP = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
PREFIX = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}"
IPV6 = r"(?:[a-fA-F0-9]{1,4}:|:){1,7}(?:[a-fA-F0-9]{1,4}|:?)"
PREFIXV6 = r"(?:[a-fA-F0-9]{1,4}:|:){1,7}(?:[a-fA-F0-9]{1,4}|:?)/[0-9]{1,3}"
_line_ = r".+"
WORD = r"\S+"
MAC = r"(?:[0-9a-fA-F]{2}(:|\.)){5}([0-9a-fA-F]{2})|(?:[0-9a-fA-F]{4}(:|\.)){2}([0-9a-fA-F]{4})"


def get(name):
    try:
        re = globals()[name]
        return re
    except KeyError:
        return False