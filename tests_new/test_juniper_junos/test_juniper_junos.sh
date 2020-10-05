#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& cd .. \
&& echo "Juniper vMX" \
&& py.test -s -x -v test_netmiko_show.py --test_device juniper_vmx \
&& py.test -s -x -v test_netmiko_config.py --test_device juniper_vmx \
&& py.test -s -x -v test_netmiko_config_acl.py --test_device juniper_vmx \
&& py.test -s -x -v test_netmiko_commit.py --test_device juniper_vmx \
&& py.test -s -x -v test_netmiko_scp.py --test_device juniper_vmx \
&& py.test -s -x -v test_netmiko_autodetect.py --test_device juniper_vmx \
|| RETURN_CODE=1

exit $RETURN_CODE

