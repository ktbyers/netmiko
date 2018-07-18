#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Cisco IOS SSH" \
&& date \
&& py.test -v test_netmiko_show.py --test_device cisco881_fast \
&& date \
&& py.test -v test_netmiko_config.py --test_device cisco881_fast \
&& date \
|| RETURN_CODE=1

exit $RETURN_CODE
