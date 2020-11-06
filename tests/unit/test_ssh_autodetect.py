#!/usr/bin/env python
from netmiko.ssh_autodetect import SSH_MAPPER_BASE


def test_ssh_base_mapper_order():
    "SSH_MAPPER_BASE should be sorted based on the most common command used." ""
    assert SSH_MAPPER_BASE[0][1]["cmd"] == "show version"
