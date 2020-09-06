#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& cd .. \
&& echo "Cisco IOS-XE" \
&& py.test -v test_netmiko_show.py --test_device cisco3 \
&& py.test -v test_netmiko_config.py --test_device cisco3 \
&& py.test -v test_netmiko_config_acl.py --test_device cisco3 \
&& py.test -v test_netmiko_scp.py --test_device cisco3 \
|| RETURN_CODE=1

exit $RETURN_CODE
