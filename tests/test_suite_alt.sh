#!/bin/sh

RETURN_CODE=0
PYTEST='py.test -s -v -x'

# Exit on the first test failure and set RETURN_CODE = 1
echo "Starting tests...good luck:" \
\
&& echo "Cisco IOS-XE SSH (including SCP)" \
&& $PYTEST test_netmiko_scp.py --test_device cisco3 \
&& $PYTEST test_netmiko_show.py --test_device cisco3 \
&& $PYTEST test_netmiko_config.py --test_device cisco3 \
&& $PYTEST test_netmiko_config_acl.py --test_device cisco3 \
\
&& echo "Cisco IOS-XE and IOS-XR Long Name Test" \
&& $PYTEST test_netmiko_config.py --test_device cisco3_long_name \
&& $PYTEST test_netmiko_config.py --test_device cisco_xr_long_name \
\
&& echo "Exception and Timeout Tests" \
&& $PYTEST test_netmiko_exceptions.py \
\
&& echo "Juniper vMX" \
&& $PYTEST test_netmiko_show.py --test_device juniper_vmx \
&& $PYTEST test_netmiko_config.py --test_device juniper_vmx \
\
&& echo "Cisco IOS-XR (Azure)" \
&& $PYTEST test_netmiko_show.py --test_device cisco_xr_azure \
&& $PYTEST test_netmiko_config.py --test_device cisco_xr_azure \
&& $PYTEST test_netmiko_commit.py --test_device cisco_xr_azure \
\
&& echo "Cisco IOS SSH (including SCP) using key auth" \
&& $PYTEST test_netmiko_tcl.py --test_device cisco881_key \
&& $PYTEST test_netmiko_show.py --test_device cisco881_key \
&& $PYTEST test_netmiko_config.py --test_device cisco881_key \
&& $PYTEST test_netmiko_config_acl.py --test_device cisco881_key \
\
&& echo "Cisco IOS SSH (including SCP)" \
&& $PYTEST test_netmiko_tcl.py --test_device cisco1 \
&& $PYTEST test_netmiko_show.py --test_device cisco1 \
&& $PYTEST test_netmiko_config.py --test_device cisco1 \
&& $PYTEST test_netmiko_config_acl.py --test_device cisco1 \
\
&& echo "Cisco IOS SSH fast_cli (including SCP)" \
&& $PYTEST test_netmiko_tcl.py --test_device cisco881_fast \
&& $PYTEST test_netmiko_show.py --test_device cisco881_fast \
&& $PYTEST test_netmiko_config.py --test_device cisco881_fast \
\
&& echo "Cisco IOS using SSH config with SSH Proxy" \
&& $PYTEST test_netmiko_show.py --test_device cisco881_ssh_config \
&& $PYTEST test_netmiko_config.py --test_device cisco881_ssh_config \
&& $PYTEST test_netmiko_config_acl.py --test_device cisco881_ssh_config \
\
&& echo "Cisco IOS using SSH config with SSH Proxy using ProxyJump" \
&& $PYTEST test_netmiko_show.py --test_device cisco881_ssh_proxyjump \
&& $PYTEST test_netmiko_config.py --test_device cisco881_ssh_proxyjump \
&& $PYTEST test_netmiko_config_acl.py --test_device cisco881_ssh_proxyjump \
\
&& echo "Cisco IOS session log testing" \
&& $PYTEST test_netmiko_session_log.py --test_device cisco881_slog \
\
&& echo "Cisco IOS telnet" \
&& $PYTEST test_netmiko_show.py --test_device cisco881_telnet \
&& $PYTEST test_netmiko_config.py --test_device cisco881_telnet \
&& $PYTEST test_netmiko_config_acl.py --test_device cisco881_telnet \
\
&& echo "Cisco SG300" \
&& $PYTEST test_netmiko_show.py --test_device cisco_s300 \
&& $PYTEST test_netmiko_config.py --test_device cisco_s300 \
\
&& echo "Arista" \
&& $PYTEST test_netmiko_scp.py --test_device arista_sw \
&& $PYTEST test_netmiko_show.py --test_device arista_sw \
&& $PYTEST test_netmiko_config.py --test_device arista_sw \
&& $PYTEST test_netmiko_config_acl.py --test_device arista_sw \
\
&& echo "Juniper" \
&& $PYTEST test_netmiko_scp.py --test_device juniper_srx \
&& $PYTEST test_netmiko_show.py --test_device juniper_srx \
&& $PYTEST test_netmiko_config.py --test_device juniper_srx \
&& $PYTEST test_netmiko_commit.py --test_device juniper_srx \
\
&& echo "Cisco IOS-XR" \
&& $PYTEST test_netmiko_scp.py --test_device cisco_xrv \
&& $PYTEST test_netmiko_show.py --test_device cisco_xrv \
&& $PYTEST test_netmiko_config.py --test_device cisco_xrv \
&& $PYTEST test_netmiko_commit.py --test_device cisco_xrv \
\
&& echo "Cisco NXOS" \
&& $PYTEST test_netmiko_scp.py --test_device nxos1 \
&& $PYTEST test_netmiko_show.py --test_device nxos1 \
&& $PYTEST test_netmiko_config.py --test_device nxos1 \
\
&& echo "Linux SSH (using keys)" \
&& $PYTEST test_netmiko_scp.py --test_device linux_srv1 \
&& $PYTEST test_netmiko_show.py --test_device linux_srv1 \
\
&& echo "Test read_timeout on Cisco3 (slow, slow, and more slow)" \
&& $PYTEST test_timeout_read_until_pattern.py --test_device cisco3 \
&& $PYTEST test_timeout_send_command.py --test_device cisco3 \
&& $PYTEST test_timeout_read_timing.py --test_device cisco3 \
&& $PYTEST test_timeout_send_command_timing.py --test_device cisco3 \
\
&& echo "Autodetect tests" \
&& $PYTEST test_netmiko_autodetect.py --test_device cisco1 \
&& $PYTEST test_netmiko_autodetect.py --test_device arista_sw \
&& $PYTEST test_netmiko_autodetect.py --test_device juniper_srx \
&& $PYTEST test_netmiko_autodetect.py --test_device cisco_asa \
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
