#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
#echo "Starting tests...good luck:" \
#&& py.test -v test_netmiko_show.py --test_device cisco881 \
#&& py.test -v test_netmiko_config.py --test_device cisco881 \
#\
#&& py.test -v test_netmiko_show.py --test_device arista_sw4 \
#&& py.test -v test_netmiko_config.py --test_device arista_sw4 \
#\
#&& py.test -v test_netmiko_show.py --test_device hp_procurve \
#&& py.test -v test_netmiko_config.py --test_device hp_procurve \
#\
#&& py.test -v test_netmiko_show.py --test_device juniper_srx \
#&& py.test -v test_netmiko_config.py --test_device juniper_srx \
#&& py.test -v test_netmiko_commit.py --test_device juniper_srx \
#\
echo "Starting tests...good luck:" \
&& py.test -s -v test_netmiko_show.py --test_device cisco_xrv \
&& py.test -v test_netmiko_config.py --test_device cisco_xrv \
&& py.test -v test_netmiko_commit.py --test_device cisco_xrv \
|| RETURN_CODE=1

#\
#&& py.test -v test_netmiko_show.py --test_device cisco_asa \
#&& py.test -v test_netmiko_config.py --test_device cisco_asa \

exit $RETURN_CODE
