#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
&& echo "Linux SSH (using keys)" \
&& py.test -s -v test_netmiko_show.py --test_device linux_srv1 \
\
&& echo "Cisco IOS SSH (including SCP)" \
&& py.test -v test_netmiko_scp.py --test_device cisco881 \
&& py.test -v test_netmiko_tcl.py --test_device cisco881 \
&& py.test -v test_netmiko_show.py --test_device cisco881 \
&& py.test -v test_netmiko_config.py --test_device cisco881 \
\
&& echo "Cisco IOS telnet" \
&& py.test -v test_netmiko_show.py --test_device cisco881_telnet \
&& py.test -v test_netmiko_config.py --test_device cisco881_telnet \
\
&& echo "Cisco SG300" \
&& py.test -v test_netmiko_show.py --test_device cisco_s300 \
&& py.test -v test_netmiko_config.py --test_device cisco_s300 \
\
&& echo "Arista" \
&& py.test -v test_netmiko_show.py --test_device arista_sw4 \
&& py.test -v test_netmiko_config.py --test_device arista_sw4 \
\
&& echo "HP ProCurve" \
&& py.test -v test_netmiko_show.py --test_device hp_procurve \
&& py.test -v test_netmiko_config.py --test_device hp_procurve \
\
&& echo "Juniper" \
&& py.test -v test_netmiko_show.py --test_device juniper_srx \
&& py.test -v test_netmiko_config.py --test_device juniper_srx \
&& py.test -v test_netmiko_commit.py --test_device juniper_srx \
\
&& echo "Cisco ASA" \
&& py.test -v test_netmiko_show.py --test_device cisco_asa \
&& py.test -v test_netmiko_config.py --test_device cisco_asa \
\
&& echo "Cisco IOS-XR" \
&& py.test -v test_netmiko_show.py --test_device cisco_xrv \
&& py.test -v test_netmiko_config.py --test_device cisco_xrv \
&& py.test -v test_netmiko_commit.py --test_device cisco_xrv \
\
&& echo "Autodetect tests" \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco881 \
&& py.test -s -v test_netmiko_autodetect.py --test_device arista_sw4 \
&& py.test -s -v test_netmiko_autodetect.py --test_device juniper_srx \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco_asa \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco_xrv \
\
|| RETURN_CODE=1

exit $RETURN_CODE

#\
#&& echo "HP Comware7" \
#&& py.test -v test_netmiko_show.py --test_device hp_comware \
#&& py.test -v test_netmiko_config.py --test_device hp_comware \
