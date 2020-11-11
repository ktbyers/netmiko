#!/bin/sh

RETURN_CODE=0

echo "Starting tests...good luck:" \
&& echo "Cisco ASA" \
&& cd .. \
&& py.test -s -v -x test_netmiko_show.py --test_device cisco_asa \
&& py.test -s -v -x test_netmiko_config.py --test_device cisco_asa \
&& py.test -s -x -v test_netmiko_scp.py --test_device cisco_asa \
&& py.test -s -v -x test_netmiko_autodetect.py --test_device cisco_asa \
|| RETURN_CODE=1

exit $RETURN_CODE

# NEED SCP
# NEED ASA login code
# NEED long ACL test code
# Newline normalization has a problem here in session_log
# Test "login" process
# Strongly consider making that new enable with cmd_verify baked in the new cmd_verify
# Strongly consider making that check_config_mode with a pattern backed in the new normal (potentially abstracting the prompts
# to attributes)
