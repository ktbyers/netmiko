#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& cd .. \
&& echo "Cisco IOS-XR (Azure)" \
&& py.test -s -x -v test_netmiko_show.py --test_device cisco_xr_azure \
&& py.test -s -x -v test_netmiko_config.py --test_device cisco_xr_azure \
&& py.test -s -x -v test_netmiko_commit.py --test_device cisco_xr_azure \
&& py.test -s -x -v test_netmiko_autodetect.py --test_device cisco_xr_azure \
\
|| RETURN_CODE=1

exit $RETURN_CODE

# FIX - some issue with SCP to the IOS-XR in Azure?
#&& py.test -s -x -v test_netmiko_scp.py --test_device cisco_xr_azure \
