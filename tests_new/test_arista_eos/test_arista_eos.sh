#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Arista EOS" \
&& cd .. \
&& py.test -s -x -v test_netmiko_show.py --test_device arista_sw \
&& py.test -s -x -v test_netmiko_config.py --test_device arista_sw \
&& py.test -s -x -v test_netmiko_config_acl.py --test_device arista_sw \
&& py.test -s -x -v test_netmiko_scp.py --test_device arista_sw \
&& py.test -s -x -v test_netmiko_autodetect.py --test_device arista_sw \
|| RETURN_CODE=1

exit $RETURN_CODE
