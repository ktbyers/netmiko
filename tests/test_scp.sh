#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "SCP Tests" \
&& py.test test_netmiko_scp.py::test_file_transfer --test_device cisco881 \
&& py.test test_netmiko_scp.py::test_file_transfer --test_device nxos1 \
&& py.test -s -v test_netmiko_scp.py::test_file_transfer --test_device arista_sw \
&& py.test -s -v test_netmiko_scp.py::test_file_transfer --test_device juniper_srx \
&& py.test -s -v test_netmiko_scp.py::test_file_transfer --test_device cisco_xrv \
|| RETURN_CODE=1

exit $RETURN_CODE
