#!/bin/sh

RETURN_CODE=0

echo "Starting tests...:" \
&& echo "Nokia SR Linux" \
&& cd .. \
&& pytest -s -x -v test_netmiko_show.py --test_device nokia_srl \
&& pytest -s -x -v test_netmiko_config.py --test_device nokia_srl \
|| RETURN_CODE=1

exit $RETURN_CODE
