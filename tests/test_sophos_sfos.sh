#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Sophos SFOS SSH" \
&& date \
&& py.test -v test_netmiko_show.py --test_device sophos_sfos \
&& date \
|| RETURN_CODE=1

exit $RETURN_CODE
