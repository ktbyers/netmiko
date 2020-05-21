#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
&& echo "Ubiquiti UniFi Switch" \
&& py.test -v test_netmiko_show.py --test_device ubiquiti_unifi \
&& py.test -v test_netmiko_config.py --test_device ubiquiti_unifi \
|| RETURN_CODE=1

exit $RETURN_CODE
