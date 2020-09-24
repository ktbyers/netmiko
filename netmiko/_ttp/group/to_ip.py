def to_ip(data, ip_key, mask_key):
    """This method takes ip_key and mask_key and tries to
    convert them into ip object
    """
    if ip_key in data and mask_key in data:
        ip_string = "{}/{}".format(data[ip_key], data[mask_key])
        try:
            data[ip_key] = _ttp_["match"]["to_ip"](ip_string)[0]
        except:
            pass
    return data, None