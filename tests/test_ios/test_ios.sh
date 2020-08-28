#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Cisco IOS" \
&& cd .. \
&& py.test -s -x -v test_netmiko_show.py --test_device cisco881 \
&& py.test -s -x -v test_netmiko_config.py --test_device cisco881 \
&& py.test -s -x -v test_netmiko_config_acl.py --test_device cisco881 \
&& py.test -s -x -v test_netmiko_tcl.py --test_device cisco881 \
&& py.test -s -x -v test_netmiko_scp.py --test_device cisco881 \
|| RETURN_CODE=1

exit $RETURN_CODE

#&& py.test -v test_netmiko_tcl.py --test_device cisco881_key \
#&& py.test -v test_netmiko_show.py --test_device cisco881_key \
#&& py.test -v test_netmiko_config.py --test_device cisco881_key \
#&& py.test -v test_netmiko_config_acl.py --test_device cisco881_key \

#&& py.test -v test_netmiko_session_log.py --test_device cisco881_slog \

#&& py.test -v test_netmiko_tcl.py --test_device cisco881_fast \
#&& py.test -v test_netmiko_show.py --test_device cisco881_fast \
#&& py.test -v test_netmiko_config.py --test_device cisco881_fast \

#&& py.test -v test_netmiko_show.py --test_device cisco881_ssh_config \
#&& py.test -v test_netmiko_config.py --test_device cisco881_ssh_config \
#&& py.test -v test_netmiko_config_acl.py --test_device cisco881_ssh_config \

#&& py.test -v test_netmiko_show.py --test_device cisco881_ssh_proxyjump \
#&& py.test -v test_netmiko_config.py --test_device cisco881_ssh_proxyjump \
#&& py.test -v test_netmiko_config_acl.py --test_device cisco881_ssh_proxyjump \

#&& py.test -v test_netmiko_show.py --test_device cisco881_telnet \
#&& py.test -v test_netmiko_config.py --test_device cisco881_telnet \
#&& py.test -v test_netmiko_config_acl.py --test_device cisco881_telnet \
#&& py.test -s -v test_netmiko_autodetect.py --test_device cisco881 \

## && py.test -v test_netmiko_scp.py --test_device cisco881_key \
## && py.test -v test_netmiko_scp.py --test_device cisco881_fast \
