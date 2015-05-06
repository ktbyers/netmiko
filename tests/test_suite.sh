#!/bin/sh

py.test -v test_netmiko_show.py --test_device cisco881
py.test -v test_netmiko_config.py --test_device cisco881

#py.test -v test_netmiko_show.py --test_device cisco_asa
#py.test -v test_netmiko_config.py --test_device cisco_asa

py.test -v test_netmiko_show.py --test_device arista_sw4
py.test -v test_netmiko_config.py --test_device arista_sw4

py.test -v test_netmiko_show.py --test_device hp_procurve
py.test -v test_netmiko_config.py --test_device hp_procurve

py.test -v test_netmiko_show.py --test_device juniper_srx
py.test -v test_netmiko_config.py --test_device juniper_srx
py.test -v test_netmiko_commit.py --test_device juniper_srx

