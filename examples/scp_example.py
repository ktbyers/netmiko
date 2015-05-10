#!/usr/bin/env python
'''
Cisco IOS only

Requires scp https://github.com/jbardin/scp.py
'''

from netmiko import ConnectHandler, SCPConn
from SECRET_DEVICE_CREDS import cisco_881

def main():
    '''
    SCP transfer cisco_logging.txt to network device

    Use ssh_conn as ssh channel into network device
    scp_conn must be closed after file transfer
    '''
    ssh_conn = ConnectHandler(**cisco_881)
    scp_conn = SCPConn(ssh_conn)
    s_file = 'cisco_logging.txt'
    d_file = 'cisco_logging.txt'

    print "\n\n"

    scp_conn.scp_transfer_file(s_file, d_file)
    scp_conn.close()

    output = ssh_conn.send_command("show flash: | inc cisco_logging")
    print ">> " + output + '\n'

    # Disable file copy confirmation
    output = ssh_conn.send_config_set(["file prompt quiet"])

    # Execute config merge
    print "Performing config merge\n"
    output = ssh_conn.send_command("copy flash:cisco_logging.txt running-config")

    # Verify change
    print "Verifying logging buffer change"
    output = ssh_conn.send_command("show run | inc logging buffer")
    print ">> " + output + '\n'

    # Restore copy confirmation
    output = ssh_conn.send_config_set(["file prompt alert"])


if __name__ == "__main__":
    main()
