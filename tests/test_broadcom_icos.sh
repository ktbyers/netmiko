#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
&& echo "Broadcom Icos" \
&& py.test -v test_netmiko_show.py --test_device broadcom_icos \
&& py.test -v test_netmiko_config.py --test_device broadcom_icos \
|| RETURN_CODE=1

exit $RETURN_CODE
