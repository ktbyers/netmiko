#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Cisco NXOS" \
&& py.test -v test_netmiko_scp.py --test_device nxos1 \
&& py.test -v test_netmiko_show.py --test_device nxos1 \
&& py.test -v test_netmiko_config.py --test_device nxos1 \
|| RETURN_CODE=1

exit $RETURN_CODE
