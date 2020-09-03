#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Cisco NXOS" \
&& cd .. \
&& py.test -v -s -x test_netmiko_show.py --test_device nxos1 \
&& py.test -v -s -x test_netmiko_config.py --test_device nxos1 \
&& py.test -v -s -x test_netmiko_config_acl.py --test_device nxos1 \
&& py.test -v -s -x test_netmiko_scp.py --test_device nxos1 \
|| RETURN_CODE=1

exit $RETURN_CODE
