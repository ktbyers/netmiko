#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
&& echo "Autodetect tests" \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco881 \
&& py.test -s -v test_netmiko_autodetect.py --test_device arista_sw \
&& py.test -s -v test_netmiko_autodetect.py --test_device juniper_srx \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco_asa \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco_xrv \
\
|| RETURN_CODE=1

exit $RETURN_CODE

