#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Cisco ASA" \
&& cd .. \
&& py.test -s -v -x test_netmiko_show.py --test_device cisco_asa \
&& py.test -s -v -x test_netmiko_config.py --test_device cisco_asa \
&& py.test -s -x -v test_netmiko_scp.py --test_device cisco_asa \
&& py.test -s -x -v test_netmiko_config_acl.py --test_device cisco_asa \
&& py.test -s -v -x test_netmiko_autodetect.py --test_device cisco_asa \
&& py.test -s -v -x test_netmiko_show.py --test_device cisco_asa_login \
&& py.test -s -v -x test_netmiko_config.py --test_device cisco_asa_login \
|| RETURN_CODE=1

exit $RETURN_CODE
