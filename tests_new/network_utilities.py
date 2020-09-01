from ipaddress import ip_address


def generate_ios_acl(entries=100):
    base_cmd = "ip access-list extended netmiko_test_large_acl"
    acl = [base_cmd]
    for i in range(1, entries + 1):
        cmd = f"permit ip host {ip_address('192.168.0.0') + i} any"
        acl.append(cmd)
    return acl


def generate_nxos_acl(entries=100):
    base_cmd = "ip access-list netmiko_test_large_acl"
    acl = [base_cmd]
    for i in range(1, entries + 1):
        cmd = f"permit ip host {ip_address('192.168.0.0') + i} any"
        acl.append(cmd)
    return acl
