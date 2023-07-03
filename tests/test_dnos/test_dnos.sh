#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Drivenets DNOS" \
&& cd .. \
&& py.test -s -x -v test_netmiko_show.py --test_device dnos \
|| RETURN_CODE=1

exit $RETURN_CODE
