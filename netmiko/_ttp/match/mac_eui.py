"""
Function to convert MAC address onti EUI style format.

Creds to https://stackoverflow.com/a/29446103 unswers on stackoeverflow
and NAPALM base helpers module
"""


from re import sub


def mac_eui(data):
    mac = str(data)
    # remove delimiters and convert to lower case
    mac = sub("[.:-]", "", mac).lower()
    # mac should only contain letters and numbers, also
    # if length now not 12 (eg. 008041aefd7e), staff up to
    # 12 with "0" - can happen with some vendors
    if mac.isalnum():
        if not len(mac) == 12:
            mac += "0" * (12 - len(mac))
    else:
        return data, None
    # convert mac in canonical form (eg. 00:80:41:ae:fd:7e)
    mac = ":".join([mac[i : i + 2] for i, j in enumerate(mac) if not (i % 2)])
    return mac, None