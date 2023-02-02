#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
&& echo "Dell SONiC Networking" \
&& py.test -v test_netmiko_show.py --test_device dell_sonic \
&& py.test -v test_netmiko_config.py --test_device dell_sonic \
&& py.test -v test_netmiko_scp.py --test_device dell_sonic \
|| RETURN_CODE=1

exit $RETURN_CODE
