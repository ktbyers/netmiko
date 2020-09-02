from ipaddress import ip_address


def generate_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd="ip access-list extended",
    base_addr="192.168.0.0",
):
    cmd = f"{base_cmd} {acl_name}"
    acl = [cmd]
    for i in range(1, entries + 1):
        addr = ip_address(base_addr)
        cmd = f"permit ip host {addr + i} any"
        acl.append(cmd)
    return acl


def generate_ios_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd="ip access-list extended",
    base_addr="192.168.0.0",
):
    return generate_acl(
        acl_name=acl_name, entries=entries, base_cmd=base_cmd, base_addr=base_addr
    )


def generate_nxos_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd="ip access-list",
    base_addr="192.168.0.0",
):
    return generate_acl(
        acl_name=acl_name, entries=entries, base_cmd=base_cmd, base_addr=base_addr
    )


if __name__ == "__main__":
    # Test code
    acl = generate_ios_acl(entries=10)
    ios_ref_acl = [
        "ip access-list extended netmiko_test_large_acl",
        "permit ip host 192.168.0.1 any",
        "permit ip host 192.168.0.2 any",
        "permit ip host 192.168.0.3 any",
        "permit ip host 192.168.0.4 any",
        "permit ip host 192.168.0.5 any",
        "permit ip host 192.168.0.6 any",
        "permit ip host 192.168.0.7 any",
        "permit ip host 192.168.0.8 any",
        "permit ip host 192.168.0.9 any",
        "permit ip host 192.168.0.10 any",
    ]

    assert acl == ios_ref_acl

    acl = generate_nxos_acl(entries=10)
    nxos_ref_acl = [
        "ip access-list netmiko_test_large_acl",
        "permit ip host 192.168.0.1 any",
        "permit ip host 192.168.0.2 any",
        "permit ip host 192.168.0.3 any",
        "permit ip host 192.168.0.4 any",
        "permit ip host 192.168.0.5 any",
        "permit ip host 192.168.0.6 any",
        "permit ip host 192.168.0.7 any",
        "permit ip host 192.168.0.8 any",
        "permit ip host 192.168.0.9 any",
        "permit ip host 192.168.0.10 any",
    ]
    assert acl == nxos_ref_acl
