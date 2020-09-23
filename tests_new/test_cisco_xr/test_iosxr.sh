#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Cisco IOS-XR (xrv)" \
&& cd .. \
&& py.test -s -x -v test_netmiko_show.py --test_device cisco_xrv \
&& py.test -s -x -v test_netmiko_config.py --test_device cisco_xrv \
&& py.test -v -s -x test_netmiko_config_acl.py --test_device cisco_xrv \
&& py.test -s -x -v test_netmiko_commit.py --test_device cisco_xrv \
&& py.test -s -x -v test_netmiko_scp.py --test_device cisco_xrv \
&& py.test -s -x -v test_netmiko_autodetect.py --test_device cisco_xrv \
|| RETURN_CODE=1

exit $RETURN_CODE
