#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck: (SR-OS CLI)" \
&& echo "SR-OS CLI" \
&& py.test -x -s -v test_netmiko_show.py --test_device sros2 \
&& py.test -x -s -v test_netmiko_config.py --test_device sros2 \
&& py.test -x -s -v test_netmiko_scp.py --test_device sros2 \
\
&& echo "SR-OS MD" \
&& py.test -x -s -v test_netmiko_show.py --test_device sros1_md \
&& py.test -x -s -v test_netmiko_config.py --test_device sros1_md \
&& py.test -x -s -v test_netmiko_scp.py --test_device sros1_md \
&& py.test -x -s -v test_netmiko_commit.py --test_device sros1_md \
|| RETURN_CODE=1

exit $RETURN_CODE
