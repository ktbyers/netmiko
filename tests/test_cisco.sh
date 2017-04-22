#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Cisco IOS SSH (including SCP) using key auth" \
&& py.test -v test_netmiko_scp.py --test_device cisco881_key \
&& py.test -v test_netmiko_tcl.py --test_device cisco881_key \
&& py.test -v test_netmiko_show.py --test_device cisco881_key \
&& py.test -v test_netmiko_config.py --test_device cisco881_key \
|| RETURN_CODE=1

exit $RETURN_CODE
