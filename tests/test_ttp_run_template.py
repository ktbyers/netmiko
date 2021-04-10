import sys
import pytest

sys.path.insert(0, "..")  # need it to run "python test_ttp_run_template.py"

from netmiko import ConnectHandler  # noqa

try:
    from ttp import ttp  # noqa

    TTP_INSTALLED = True

except ImportError:
    TTP_INSTALLED = False

try:
    from ttp_templates import get_template  # noqa

    TTP_TEMPLATES_INSTALLED = True

except ImportError:
    TTP_TEMPLATES_INSTALLED = False

skip_if_no_ttp = pytest.mark.skipif(
    TTP_INSTALLED is False, reason="Failed to import TTP module"
)
skip_if_no_ttp_templates = pytest.mark.skipif(
    TTP_TEMPLATES_INSTALLED is False, reason="Failed to import TTP templates module"
)

lab = {
    "device_type": "cisco_ios",
    "host": "1.2.3.4",
    "username": "cisco",
    "password": "cisco",
    "auto_connect": False,  # stop Netmiko trying connect to device
}


@skip_if_no_ttp
def mock_output(command_string, *args, **kwargs):
    outputs = {
        "show run | inc ntp": """
ntp server 8.8.8.8
ntp server 7.7.7.8
ntp server 1.1.1.2
ntp server 3.3.3.3
ntp server 7.7.7.7
        """,
        "show run | inc aaa": """
aaa new-model
aaa authentication login default local
aaa authorization exec default local
aaa session-id common
        """,
        "show run | sec interface": """
interface Loopback0
 description Routing Loopback
 ip address 10.0.0.10 255.255.255.255
 ip ospf 1 area 0
 ipv6 address 2001::10/128
interface Loopback100
 ip address 1.1.1.100 255.255.255.255
interface Ethernet0/0
 description Main Interface for L3 features testing
 no ip address
 duplex auto
interface Ethernet0/0.102
 description to_vIOS1_Gi0/0.102
 encapsulation dot1Q 102
 ip address 10.1.102.10 255.255.255.0
 ipv6 address 2001:102::10/64
interface Ethernet0/0.107
 description to_IOL2_Eth0/0.107
 encapsulation dot1Q 107
 ip address 10.1.107.10 255.255.255.0
 ip ospf network point-to-point
 ip ospf 1 area 0
 ipv6 address 2001:107::10/64
interface Ethernet0/0.2000
 encapsulation dot1Q 2000
 vrf forwarding MGMT
 ip address 192.168.217.10 255.255.255.0
interface Ethernet0/1
 no ip address
 duplex auto
interface Ethernet0/2
 no ip address
 duplex auto
interface Ethernet0/3
 no ip address
 shutdown
 duplex auto
        """,
    }
    return outputs[command_string]


connection = ConnectHandler(**lab)

# override send command method to return mock data
setattr(connection, "send_command", mock_output)


@skip_if_no_ttp
def test_run_ttp_template_from_text():
    template = """
<input name="ntp_and_aaa" load="yaml">
commands:
  - show run | inc ntp
  - show run | inc aaa
</input>

<input name="interfaces_cfg">
commands = [
    "show run | sec interface"
]
</input>

<group name="misc" input="ntp_and_aaa">
ntp server {{ ntp_servers | joinmatches(",") }}
aaa authentication login {{ authen | PHRASE }}
aaa authorization exec {{ author_exec | PHRASE }}
</group>

<group name="interfaces" input="interfaces_cfg">
interface {{ interface }}
 description {{ description | re(".+") }}
 encapsulation dot1Q {{ dot1q }}
 ip address {{ ip }} {{ mask }}
</group>
    """
    res = connection.run_ttp(template)
    assert res == [
        [
            {
                "misc": [
                    {"ntp_servers": "8.8.8.8"},
                    {"ntp_servers": "7.7.7.8"},
                    {"ntp_servers": "1.1.1.2"},
                    {"ntp_servers": "3.3.3.3"},
                    {
                        "authen": "default local",
                        "author_exec": "default local",
                        "ntp_servers": "7.7.7.7",
                    },
                ]
            },
            {
                "interfaces": [
                    {
                        "description": "Routing Loopback",
                        "interface": "Loopback0",
                        "ip": "10.0.0.10",
                        "mask": "255.255.255.255",
                    },
                    {
                        "interface": "Loopback100",
                        "ip": "1.1.1.100",
                        "mask": "255.255.255.255",
                    },
                    {
                        "description": "Main Interface for L3 features testing",
                        "interface": "Ethernet0/0",
                    },
                    {
                        "description": "to_vIOS1_Gi0/0.102",
                        "dot1q": "102",
                        "interface": "Ethernet0/0.102",
                        "ip": "10.1.102.10",
                        "mask": "255.255.255.0",
                    },
                    {
                        "description": "to_IOL2_Eth0/0.107",
                        "dot1q": "107",
                        "interface": "Ethernet0/0.107",
                        "ip": "10.1.107.10",
                        "mask": "255.255.255.0",
                    },
                    {
                        "dot1q": "2000",
                        "interface": "Ethernet0/0.2000",
                        "ip": "192.168.217.10",
                        "mask": "255.255.255.0",
                    },
                    {"interface": "Ethernet0/1"},
                    {"interface": "Ethernet0/2"},
                    {"interface": "Ethernet0/3"},
                ]
            },
        ]
    ]


@skip_if_no_ttp
def test_run_ttp_template_from_text_with_res_kwargs():
    template = """
<input name="ntp_and_aaa" load="yaml">
commands:
  - show run | inc ntp
  - show run | inc aaa
</input>

<input name="interfaces_cfg">
commands = [
    "show run | sec interface"
]
</input>

<group name="misc" input="ntp_and_aaa">
ntp server {{ ntp_servers | joinmatches(",") }}
aaa authentication login {{ authen | PHRASE }}
aaa authorization exec {{ author_exec | PHRASE }}
</group>

<group name="interfaces" input="interfaces_cfg">
interface {{ interface }}
 description {{ description | re(".+") }}
 encapsulation dot1Q {{ dot1q }}
 ip address {{ ip }} {{ mask }}
</group>
    """
    res = connection.run_ttp(template, res_kwargs={"structure": "flat_list"})
    assert res == [
        {
            "misc": [
                {"ntp_servers": "8.8.8.8"},
                {"ntp_servers": "7.7.7.8"},
                {"ntp_servers": "1.1.1.2"},
                {"ntp_servers": "3.3.3.3"},
                {
                    "authen": "default local",
                    "author_exec": "default local",
                    "ntp_servers": "7.7.7.7",
                },
            ]
        },
        {
            "interfaces": [
                {
                    "description": "Routing Loopback",
                    "interface": "Loopback0",
                    "ip": "10.0.0.10",
                    "mask": "255.255.255.255",
                },
                {
                    "interface": "Loopback100",
                    "ip": "1.1.1.100",
                    "mask": "255.255.255.255",
                },
                {
                    "description": "Main Interface for L3 features testing",
                    "interface": "Ethernet0/0",
                },
                {
                    "description": "to_vIOS1_Gi0/0.102",
                    "dot1q": "102",
                    "interface": "Ethernet0/0.102",
                    "ip": "10.1.102.10",
                    "mask": "255.255.255.0",
                },
                {
                    "description": "to_IOL2_Eth0/0.107",
                    "dot1q": "107",
                    "interface": "Ethernet0/0.107",
                    "ip": "10.1.107.10",
                    "mask": "255.255.255.0",
                },
                {
                    "dot1q": "2000",
                    "interface": "Ethernet0/0.2000",
                    "ip": "192.168.217.10",
                    "mask": "255.255.255.0",
                },
                {"interface": "Ethernet0/1"},
                {"interface": "Ethernet0/2"},
                {"interface": "Ethernet0/3"},
            ]
        },
    ]


@skip_if_no_ttp
def test_run_ttp_template_from_file():
    template = "./test_ttp_run_template_1.txt"
    res = connection.run_ttp(template)
    assert res == [
        [
            {
                "misc": [
                    {"ntp_servers": "8.8.8.8"},
                    {"ntp_servers": "7.7.7.8"},
                    {"ntp_servers": "1.1.1.2"},
                    {"ntp_servers": "3.3.3.3"},
                    {
                        "authen": "default local",
                        "author_exec": "default local",
                        "ntp_servers": "7.7.7.7",
                    },
                ]
            },
            {
                "interfaces": [
                    {
                        "description": "Routing Loopback",
                        "interface": "Loopback0",
                        "ip": "10.0.0.10",
                        "mask": "255.255.255.255",
                    },
                    {
                        "interface": "Loopback100",
                        "ip": "1.1.1.100",
                        "mask": "255.255.255.255",
                    },
                    {
                        "description": "Main Interface for L3 features testing",
                        "interface": "Ethernet0/0",
                    },
                    {
                        "description": "to_vIOS1_Gi0/0.102",
                        "dot1q": "102",
                        "interface": "Ethernet0/0.102",
                        "ip": "10.1.102.10",
                        "mask": "255.255.255.0",
                    },
                    {
                        "description": "to_IOL2_Eth0/0.107",
                        "dot1q": "107",
                        "interface": "Ethernet0/0.107",
                        "ip": "10.1.107.10",
                        "mask": "255.255.255.0",
                    },
                    {
                        "dot1q": "2000",
                        "interface": "Ethernet0/0.2000",
                        "ip": "192.168.217.10",
                        "mask": "255.255.255.0",
                    },
                    {"interface": "Ethernet0/1"},
                    {"interface": "Ethernet0/2"},
                    {"interface": "Ethernet0/3"},
                ]
            },
        ]
    ]


@skip_if_no_ttp
@skip_if_no_ttp_templates
def test_run_ttp_template_from_ttp_templates():
    template = "ttp://misc/ttp_templates_tests/netmiko_cisco_ios_interfaces.txt"
    res = connection.run_ttp(template)
    assert res == [
        {
            "intf_cfg": [
                {
                    "description": "Routing Loopback",
                    "interface": "Loopback0",
                    "ip": "10.0.0.10",
                    "mask": "255.255.255.255",
                },
                {
                    "interface": "Loopback100",
                    "ip": "1.1.1.100",
                    "mask": "255.255.255.255",
                },
                {
                    "description": "Main Interface for L3 features testing",
                    "interface": "Ethernet0/0",
                },
                {
                    "description": "to_vIOS1_Gi0/0.102",
                    "interface": "Ethernet0/0.102",
                    "ip": "10.1.102.10",
                    "mask": "255.255.255.0",
                },
                {
                    "description": "to_IOL2_Eth0/0.107",
                    "interface": "Ethernet0/0.107",
                    "ip": "10.1.107.10",
                    "mask": "255.255.255.0",
                },
                {
                    "interface": "Ethernet0/0.2000",
                    "ip": "192.168.217.10",
                    "mask": "255.255.255.0",
                },
                {"interface": "Ethernet0/1"},
                {"interface": "Ethernet0/2"},
                {"interface": "Ethernet0/3"},
            ]
        }
    ]


@skip_if_no_ttp
def test_run_ttp_template_default_input():
    template = """
<doc>
This template used in to test Netmiko run_ttp method
</doc>

<template name="interfaces" results="per_template">
<input>
commands = [
    "show run | sec interface"
]
</input>

<group name="intf_cfg">
interface {{ interface }}
 description {{ description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
</template>
    """
    res = connection.run_ttp(template)
    assert res == [
        {
            "intf_cfg": [
                {
                    "description": "Routing Loopback",
                    "interface": "Loopback0",
                    "ip": "10.0.0.10",
                    "mask": "255.255.255.255",
                },
                {
                    "interface": "Loopback100",
                    "ip": "1.1.1.100",
                    "mask": "255.255.255.255",
                },
                {
                    "description": "Main Interface for L3 features testing",
                    "interface": "Ethernet0/0",
                },
                {
                    "description": "to_vIOS1_Gi0/0.102",
                    "interface": "Ethernet0/0.102",
                    "ip": "10.1.102.10",
                    "mask": "255.255.255.0",
                },
                {
                    "description": "to_IOL2_Eth0/0.107",
                    "interface": "Ethernet0/0.107",
                    "ip": "10.1.107.10",
                    "mask": "255.255.255.0",
                },
                {
                    "interface": "Ethernet0/0.2000",
                    "ip": "192.168.217.10",
                    "mask": "255.255.255.0",
                },
                {"interface": "Ethernet0/1"},
                {"interface": "Ethernet0/2"},
                {"interface": "Ethernet0/3"},
            ]
        }
    ]


@skip_if_no_ttp
def test_run_ttp_template_dict_struct():
    template = """
<doc>
This template used in to test Netmiko run_ttp method
</doc>

<template name="interfaces" results="per_template">
<input>
commands = [
    "show run | sec interface"
]
</input>

<group name="intf_cfg">
interface {{ interface }}
 description {{ description | ORPHRASE }}
 ip address {{ ip }} {{ mask }}
</group>
</template>
    """
    res = connection.run_ttp(template, res_kwargs={"structure": "dictionary"})
    assert res == {
        "interfaces": {
            "intf_cfg": [
                {
                    "description": "Routing Loopback",
                    "interface": "Loopback0",
                    "ip": "10.0.0.10",
                    "mask": "255.255.255.255",
                },
                {
                    "interface": "Loopback100",
                    "ip": "1.1.1.100",
                    "mask": "255.255.255.255",
                },
                {
                    "description": "Main Interface for L3 features " "testing",
                    "interface": "Ethernet0/0",
                },
                {
                    "description": "to_vIOS1_Gi0/0.102",
                    "interface": "Ethernet0/0.102",
                    "ip": "10.1.102.10",
                    "mask": "255.255.255.0",
                },
                {
                    "description": "to_IOL2_Eth0/0.107",
                    "interface": "Ethernet0/0.107",
                    "ip": "10.1.107.10",
                    "mask": "255.255.255.0",
                },
                {
                    "interface": "Ethernet0/0.2000",
                    "ip": "192.168.217.10",
                    "mask": "255.255.255.0",
                },
                {"interface": "Ethernet0/1"},
                {"interface": "Ethernet0/2"},
                {"interface": "Ethernet0/3"},
            ]
        }
    }


@skip_if_no_ttp
def test_run_ttp_template_with_errors():
    """
    Input ntp_and_aaa does not have command parameter.
    Input interfaces_cfg has wrong method.
    """
    template = """
<input name="ntp_and_aaa" load="yaml">
commmmmands:
  - show run | inc ntp
  - show run | inc aaa
</input>

<input name="interfaces_cfg">
method = "does_not_exist"
commands = [
    "show run | sec interface"
]
</input>

<group name="misc" input="ntp_and_aaa">
ntp server {{ ntp_servers | joinmatches(",") }}
aaa authentication login {{ authen | PHRASE }}
aaa authorization exec {{ author_exec | PHRASE }}
</group>

<group name="interfaces" input="interfaces_cfg">
interface {{ interface }}
 description {{ description | re(".+") }}
 encapsulation dot1Q {{ dot1q }}
 ip address {{ ip }} {{ mask }}
</group>
    """
    res = connection.run_ttp(template)
    assert res == [[]]
