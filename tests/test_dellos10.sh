#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
&& echo "Dell EMC Networking dellos10" \
&& py.test -v test_netmiko_show.py --test_device dellos10 \
&& py.test -v test_netmiko_config.py --test_device dellos10 \
&& py.test -v test_netmiko_scp.py --test_device dellos10 \
|| RETURN_CODE=1

exit $RETURN_CODE
