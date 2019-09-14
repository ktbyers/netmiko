#!/bin/sh

RETURN_CODE=0

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
&& echo "Cisco IOS SSH (including SCP) using key auth" \
&& py.test -v test_netmiko_scp.py --test_device cisco881_key \
&& py.test -v test_netmiko_tcl.py --test_device cisco881_key \
&& py.test -v test_netmiko_show.py --test_device cisco881_key \
&& py.test -v test_netmiko_config.py --test_device cisco881_key \
\
&& echo "Cisco IOS SSH (including SCP)" \
&& py.test -v test_netmiko_scp.py --test_device cisco881 \
&& py.test -v test_netmiko_tcl.py --test_device cisco881 \
&& py.test -v test_netmiko_show.py --test_device cisco881 \
&& py.test -v test_netmiko_config.py --test_device cisco881 \
\
&& echo "Cisco IOS using SSH config with SSH Proxy" \
&& py.test -v test_netmiko_show.py --test_device cisco881_ssh_config \
&& py.test -v test_netmiko_config.py --test_device cisco881_ssh_config \
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
&& py.test -v test_netmiko_scp.py --test_device arista_sw \
&& py.test -v test_netmiko_show.py --test_device arista_sw \
&& py.test -v test_netmiko_config.py --test_device arista_sw \
\
&& echo "HP ProCurve" \
&& py.test -v test_netmiko_show.py --test_device hp_procurve \
&& py.test -v test_netmiko_config.py --test_device hp_procurve \
\
&& echo "Juniper" \
&& py.test -v test_netmiko_scp.py --test_device juniper_srx \
&& py.test -v test_netmiko_show.py --test_device juniper_srx \
&& py.test -v test_netmiko_config.py --test_device juniper_srx \
&& py.test -v test_netmiko_commit.py --test_device juniper_srx \
\
&& echo "Cisco ASA" \
&& py.test -v test_netmiko_show.py --test_device cisco_asa \
&& py.test -v test_netmiko_config.py --test_device cisco_asa \
&& py.test -v test_netmiko_show.py --test_device cisco_asa_login \
&& py.test -v test_netmiko_config.py --test_device cisco_asa_login \
\
&& echo "Cisco IOS-XR" \
&& py.test -v test_netmiko_scp.py --test_device cisco_xrv \
&& py.test -v test_netmiko_show.py --test_device cisco_xrv \
&& py.test -v test_netmiko_config.py --test_device cisco_xrv \
&& py.test -v test_netmiko_commit.py --test_device cisco_xrv \
\
&& echo "Cisco NXOS" \
&& py.test -v test_netmiko_scp.py --test_device nxos1 \
&& py.test -v test_netmiko_show.py --test_device nxos1 \
&& py.test -v test_netmiko_config.py --test_device nxos1 \
\
&& echo "Linux SSH (using keys)" \
&& py.test -s -v test_netmiko_show.py --test_device linux_srv1 \
\
&& echo "Autodetect tests" \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco881 \
&& py.test -s -v test_netmiko_autodetect.py --test_device arista_sw \
&& py.test -s -v test_netmiko_autodetect.py --test_device juniper_srx \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco_asa \
&& py.test -s -v test_netmiko_autodetect.py --test_device cisco_xrv \
\
|| RETURN_CODE=1

exit $RETURN_CODE
