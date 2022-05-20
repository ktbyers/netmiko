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


def generate_hp_procurve_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd="ip access-list extended",
    base_addr="192.168.0.0",
):
    """
    Faked an ACL as did not see easy way to create ACL on my HPE device.

    Just remove and add NTP server so 100 lines of cfg changes.
    """

    base_acl = [
        "no sntp server 128.118.25.3",
        "sntp server 128.118.25.3",
    ]
    acl = []
    for _ in range(50):
        acl += base_acl
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


def generate_arista_eos_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd="ip access-list",
    base_addr="192.168.0.0",
):
    return generate_acl(
        acl_name=acl_name, entries=entries, base_cmd=base_cmd, base_addr=base_addr
    )


generate_cisco_ios_acl = generate_ios_acl
generate_cisco_xe_acl = generate_ios_acl


def generate_nxos_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd="ip access-list",
    base_addr="192.168.0.0",
):
    return generate_acl(
        acl_name=acl_name, entries=entries, base_cmd=base_cmd, base_addr=base_addr
    )


generate_cisco_nxos_acl = generate_nxos_acl


def generate_cisco_xr_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd="ipv4 access-list",
    base_addr="192.168.0.0",
):

    # Add base ACL command
    cmd = f"{base_cmd} {acl_name}"
    acl = [cmd]
    for i in range(1, entries + 1):
        addr = ip_address(base_addr)
        cmd = f"permit ipv4 host {addr + i} any"
        acl.append(cmd)
    return acl


def generate_juniper_junos_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd="set firewall family inet filter",
    base_addr="192.168.0.0",
):
    acl = []
    for i in range(1, entries + 1):
        addr = ip_address(base_addr)
        cmd = f"{base_cmd} {acl_name} term 10 from address {addr + i}"
        acl.append(cmd)
    return acl


def generate_cisco_asa_acl(
    acl_name="netmiko_test_large_acl",
    entries=100,
    base_cmd=None,
    base_addr="192.168.0.0",
):
    acl = []
    for i in range(1, entries + 1):
        addr = ip_address(base_addr)
        cmd = f"access-list {acl_name} extended permit ip host {addr + i} any"
        acl.append(cmd)
    return acl


def generate_linux_acl(
    acl_name="",
    entries=100,
    base_cmd=None,
    base_addr="",
):
    """Well, not really an ACL, but you get the idea."""
    acl = []
    for i in range(1, entries + 1):
        cmd = "head /var/log/messages"
        acl.append(cmd)
    return acl


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

    acl = generate_cisco_xr_acl(entries=10)
    xr_ref_acl = [
        "ipv4 access-list netmiko_test_large_acl",
        "permit ipv4 host 192.168.0.1 any",
        "permit ipv4 host 192.168.0.2 any",
        "permit ipv4 host 192.168.0.3 any",
        "permit ipv4 host 192.168.0.4 any",
        "permit ipv4 host 192.168.0.5 any",
        "permit ipv4 host 192.168.0.6 any",
        "permit ipv4 host 192.168.0.7 any",
        "permit ipv4 host 192.168.0.8 any",
        "permit ipv4 host 192.168.0.9 any",
        "permit ipv4 host 192.168.0.10 any",
    ]
    assert acl == xr_ref_acl

    acl = generate_juniper_junos_acl(entries=10)
    ref_acl = [
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.1",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.2",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.3",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.4",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.5",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.6",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.7",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.8",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.9",
        "set firewall family inet filter netmiko_test_large_acl term 10 from address "
        "192.168.0.10",
    ]
    assert acl == ref_acl

    acl = generate_cisco_asa_acl(entries=10)
    ref_acl = [
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.1 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.2 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.3 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.4 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.5 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.6 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.7 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.8 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.9 any",
        "access-list netmiko_test_large_acl extended permit ip host 192.168.0.10 any",
    ]
    assert acl == ref_acl

    acl = generate_linux_acl(entries=10)
    ref_acl = [
        "head /var/log/messages",
        "head /var/log/messages",
        "head /var/log/messages",
        "head /var/log/messages",
        "head /var/log/messages",
        "head /var/log/messages",
        "head /var/log/messages",
        "head /var/log/messages",
        "head /var/log/messages",
        "head /var/log/messages",
    ]
    assert acl == ref_acl
