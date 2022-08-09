#!/bin/sh

RETURN_CODE=0
PYTEST='py.test -s -v -x'

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
\
&& $PYTEST test_netmiko_autodetect.py --test_device cisco_xrv \
&& $PYTEST test_netmiko_autodetect.py --test_device cisco_xr_azure \
\
&& echo "HP ProCurve" \
&& $PYTEST test_netmiko_show.py --test_device hp_procurve \
&& $PYTEST test_netmiko_config.py --test_device hp_procurve \
\
|| RETURN_CODE=1

exit $RETURN_CODE

# && echo "HP Comware7" \
# && py.test -v test_netmiko_show.py --test_device hp_comware \
# && py.test -v test_netmiko_config.py --test_device hp_comware \
# \
# Can't get Cisco IOS and SCP get to run reliably--IOS bug?
# && py.test -v test_netmiko_scp.py --test_device cisco881_key \
# && py.test -v test_netmiko_scp.py --test_device cisco881_fast \
# && $PYTEST test_netmiko_scp.py --test_device cisco881_key \
#
#
#&& echo "Nokia SR-OS CLI" \
#&& py.test -x -s -v test_netmiko_show.py --test_device sros2 \
#&& py.test -x -s -v test_netmiko_config.py --test_device sros2 \
#&& py.test -x -s -v test_netmiko_scp.py --test_device sros2 \
#\
#&& echo "SR-OS MD" \
#&& py.test -x -s -v test_netmiko_show.py --test_device sros1_md \
#&& py.test -x -s -v test_netmiko_config.py --test_device sros1_md \
#&& py.test -x -s -v test_netmiko_scp.py --test_device sros1_md \
#&& py.test -x -s -v test_netmiko_commit.py --test_device sros1_md \
#\
# && echo "Cisco ASA" \
# && $PYTEST test_netmiko_show.py --test_device cisco_asa \
# && $PYTEST test_netmiko_config.py --test_device cisco_asa \
# && $PYTEST test_netmiko_show.py --test_device cisco_asa_login \
# && $PYTEST test_netmiko_config.py --test_device cisco_asa_login \
#\
