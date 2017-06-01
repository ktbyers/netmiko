#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Cisco IOS-XE" \
&& py.test -v test_netmiko_show.py --test_device ios_xe \
&& py.test -v test_netmiko_config.py --test_device ios_xe \
|| RETURN_CODE=1

exit $RETURN_CODE
