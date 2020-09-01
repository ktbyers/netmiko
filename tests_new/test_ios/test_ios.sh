#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Cisco IOS" \
&& cd .. \
&& py.test -s -x -v test_netmiko_show.py --test_device cisco1 \
&& py.test -s -x -v test_netmiko_config.py --test_device cisco1 \
&& py.test -s -x -v test_netmiko_config_acl.py --test_device cisco1 \
&& py.test -s -x -v test_netmiko_tcl.py --test_device cisco1 \
&& py.test -s -x -v test_netmiko_scp.py --test_device cisco1 \
|| RETURN_CODE=1

exit $RETURN_CODE
