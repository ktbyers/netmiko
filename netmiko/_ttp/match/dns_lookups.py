import dns.resolver as dnspython
import dns.reversename

_name_map_ = {"dns_forward": "dns", "dns_reverse": "rdns"}

dns_resolver_obj = dnspython.dns.resolver.Resolver()


def dns_forward(data, record="A", timeout=1, servers=[], add_field=False):
    """Performs forward dns lookup using dns_resolver_obj global object"""
    dns_resolver_obj.timeout = timeout
    if servers:
        if isinstance(servers, str):
            servers = [i.strip() for i in servers.split(",")]
        dns_resolver_obj.nameservers = sorted(servers)
    dns_resolver_obj.lifetime = timeout * len(dns_resolver_obj.nameservers)
    try:
        dns_records = [i.to_text() for i in dns_resolver_obj.query(data, record)]
        if add_field and isinstance(add_field, str):
            return data, {"new_field": {add_field: dns_records}}
        else:
            return dns_records, None
    except dnspython.dns.resolver.NXDOMAIN:
        pass
    except dnspython.dns.resolver.NoAnswer:
        pass
    except dnspython.dns.exception.Timeout:
        # re-initialize dns_resolver object, as it will fail to resolve names for
        # whatever reason after it timeouts
        globals()["dns_resolver_obj"] = dnspython.dns.resolver.Resolver()
    return data, None


def dns_reverse(data, timeout=1, servers=[], add_field=False):
    """Performs reverse dns lookup using global dns_resolver_obj
    data - ip address string, e.g. 192.168.0.1
    """
    dns_resolver_obj.timeout = timeout
    if servers:
        if isinstance(servers, str):
            servers = [i.strip() for i in servers.split(",")]
        dns_resolver_obj.nameservers = servers
    dns_resolver_obj.lifetime = timeout * len(dns_resolver_obj.nameservers)
    rev_name = dns.reversename.from_address(data)
    try:
        reverse_record = str(dns_resolver_obj.query(rev_name, "PTR")[0]).rstrip(".")
        if add_field and isinstance(add_field, str):
            return data, {"new_field": {add_field: reverse_record}}
        else:
            return reverse_record, None
    except dnspython.dns.resolver.NXDOMAIN:
        pass
    except dnspython.dns.resolver.NoAnswer:
        pass
    except dnspython.dns.exception.Timeout:
        globals()["dns_resolver_obj"] = dnspython.dns.resolver.Resolver()
    return data, None