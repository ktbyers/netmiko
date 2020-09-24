import ipaddress
import logging

log = logging.getLogger(__name__)


def to_ip(data, *args):
    # for py2 support need to convert data to unicode:
    if _ttp_["python_major_version"] is 2:
        ipaddr_data = unicode(data)
    elif _ttp_["python_major_version"] is 3:
        ipaddr_data = data
    if "ipv4" in args:
        if "/" in ipaddr_data or " " in ipaddr_data:
            return ipaddress.IPv4Interface(ipaddr_data.replace(" ", "/")), None
        else:
            return ipaddress.IPv4Address(ipaddr_data), None
    elif "ipv6" in args:
        if "/" in ipaddr_data:
            return ipaddress.IPv6Interface(ipaddr_data), None
        else:
            return ipaddress.IPv6Address(ipaddr_data), None
    elif "/" in ipaddr_data or " " in ipaddr_data:
        return ipaddress.ip_interface(ipaddr_data.replace(" ", "/")), None
    else:
        return ipaddress.ip_address(ipaddr_data), None


def is_ip(data, *args):
    try:
        _ = to_ip(data, *args)
        return data, True
    except:
        return data, False


def to_net(data, *args):
    # for py2 support need to convert data to unicode:
    if _ttp_["python_major_version"] is 2:
        ipaddr_data = unicode(data)
    elif _ttp_["python_major_version"] is 3:
        ipaddr_data = data
    if "ipv4" in args:
        return ipaddress.IPv4Network(ipaddr_data), None
    elif "ipv6" in args:
        return ipaddress.IPv6Network(ipaddr_data), None
    else:
        return ipaddress.ip_network(ipaddr_data), None


def to_cidr(data):
    """Method to convet 255.255.255.0 like mask to CIDR prefix len
    such as 24
    """
    try:
        ret = sum([bin(int(x)).count("1") for x in data.split(".")])
        return ret, None
    except:
        log.error(
            "ttp_functions.match.to_cidr: '{}' is not a valid netmask".format(data)
        )
        return data, None


def ip_info(data, *args):
    if isinstance(data, str):
        try:
            ip_obj = to_ip(data, *args)[0]
        except ValueError:
            return data, None
    else:
        ip_obj = data
    if isinstance(ip_obj, ipaddress.IPv4Interface) or isinstance(
        ip_obj, ipaddress.IPv6Interface
    ):
        ret = {
            "compressed": ip_obj.compressed,
            "exploded": ip_obj.exploded,
            "hostmask": str(ip_obj.hostmask),
            "ip": str(ip_obj.ip),
            "is_link_local": ip_obj.is_link_local,
            "is_loopback": ip_obj.is_loopback,
            "is_multicast": ip_obj.is_multicast,
            "is_private": ip_obj.is_private,
            "is_reserved": ip_obj.is_reserved,
            "is_unspecified": ip_obj.is_unspecified,
            "max_prefixlen": ip_obj.max_prefixlen,
            "netmask": str(ip_obj.netmask),
            "network": str(ip_obj.network),
            "version": ip_obj.version,
            "with_hostmask": ip_obj.with_hostmask,
            "with_netmask": ip_obj.with_netmask,
            "with_prefixlen": ip_obj.with_prefixlen,
            "broadcast_address": str(ip_obj.network.broadcast_address),
            "network_address": str(ip_obj.network.network_address),
            "num_addresses": ip_obj.network.num_addresses,
            "hosts": ip_obj.network.num_addresses - 2,
            "prefixlen": ip_obj.network.prefixlen,
        }
    elif isinstance(ip_obj, ipaddress.IPv4Address) or isinstance(
        ip_obj, ipaddress.IPv6Address
    ):
        ret = {
            "ip": str(ip_obj),
            "compressed": ip_obj.compressed,
            "exploded": ip_obj.exploded,
            "is_link_local": ip_obj.is_link_local,
            "is_loopback": ip_obj.is_loopback,
            "is_multicast": ip_obj.is_multicast,
            "is_private": ip_obj.is_private,
            "is_reserved": ip_obj.is_reserved,
            "is_unspecified": ip_obj.is_unspecified,
            "max_prefixlen": ip_obj.max_prefixlen,
            "version": ip_obj.version,
        }
    else:
        ret = data
    return ret, None


def cidr_match(data, prefix):
    # try to get value from TTP vars variables
    prefix = _ttp_["parser_object"].vars.get(prefix, prefix)
    # convert data to ipaddress object:
    if isinstance(data, str):
        try:
            ip_obj = to_ip(data)[0]
        except ValueError:
            return data, None
    else:
        ip_obj = data
    # create ipaddress ipnetwork object out of prefix
    ip_net = to_net(prefix)[0]
    if isinstance(ip_obj, ipaddress.IPv4Interface) or isinstance(
        ip_obj, ipaddress.IPv6Interface
    ):
        # if object is ipnetwork, can check it as is:
        check = ip_obj.network.overlaps(ip_net)
    elif isinstance(ip_obj, ipaddress.IPv4Address) or isinstance(
        ip_obj, ipaddress.IPv6Address
    ):
        # if object is ipaddress, need to convert it into ipinterface with /32 mask:
        if ip_obj.version is 4:
            # for py2 support need to convert data to unicode:
            if _ttp_["python_major_version"] is 2:
                ipaddr_data = unicode("{}/32".format(str(ip_obj)))
            elif _ttp_["python_major_version"] is 3:
                ipaddr_data = "{}/32".format(str(ip_obj))
            ip_obj = ipaddress.IPv4Interface(ipaddr_data)
        elif ip_obj.version is 6:
            # for py2 support need to convert data to unicode:
            if _ttp_["python_major_version"] is 2:
                ipaddr_data = unicode("{}/128".format(str(ip_obj)))
            elif _ttp_["python_major_version"] is 3:
                ipaddr_data = "{}/128".format(str(ip_obj))
            ip_obj = ipaddress.IPv6Interface(ipaddr_data)
        check = ip_obj.network.overlaps(ip_net)
    else:
        check = None
    return data, check