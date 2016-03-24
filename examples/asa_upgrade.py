#!/usr/bin/env python
"""Script to upgrade a Cisco ASA."""
import sys
from datetime import datetime
from getpass import getpass
from netmiko import ConnectHandler, FileTransfer

def asa_scp_handler(ssh_conn, cmd='ssh scopy enable', mode='enable'):
    """Enable/disable SCP on Cisco ASA."""
    if mode == 'disable':
        cmd = 'no ' + cmd
    return ssh_conn.send_config_set([cmd])

def main():
    """Script to upgrade a Cisco ASA."""
    ip_addr = raw_input("Enter ASA IP address: ")
    my_pass = getpass()
    start_time = datetime.now()
    print ">>>> {}".format(start_time)

    net_device = {
        'device_type': 'cisco_asa',
        'ip': ip_addr,
        'username': 'admin',
        'password': my_pass,
        'secret': my_pass,
        'port': 22,
    }

    print "\nLogging in to ASA"
    ssh_conn = ConnectHandler(**net_device)
    print

    # ADJUST TO TRANSFER IMAGE FILE
    dest_file_system = 'disk0:'
    source_file = 'test1.txt'
    dest_file = 'test1.txt'
    alt_dest_file = 'asa825-59-k8.bin'
    scp_changed = False

    with FileTransfer(ssh_conn, source_file=source_file, dest_file=dest_file,
                      file_system=dest_file_system) as scp_transfer:

        if not scp_transfer.check_file_exists():
            if not scp_transfer.verify_space_available():
                raise ValueError("Insufficient space available on remote device")

            print "Enabling SCP"
            output = asa_scp_handler(ssh_conn, mode='enable')
            print output

            print "\nTransferring file\n"
            scp_transfer.transfer_file()

            print "Disabling SCP"
            output = asa_scp_handler(ssh_conn, mode='disable')
            print output

        print "\nVerifying file"
        if scp_transfer.verify_file():
            print "Source and destination MD5 matches"
        else:
            raise ValueError("MD5 failure between source and destination files")

    print "\nSending boot commands"
    full_file_name = "{}/{}".format(dest_file_system, alt_dest_file)
    boot_cmd = 'boot system {}'.format(full_file_name)
    output = ssh_conn.send_config_set([boot_cmd])
    print output

    print "\nVerifying state"
    output = ssh_conn.send_command('show boot')
    print output

    # UNCOMMENT TO PERFORM WR MEM AND RELOAD
    #print "\nWrite mem and reload"
    #output = ssh_conn.send_command_expect('write mem')
    #output += ssh_conn.send_command('reload')
    #output += ssh_conn.send_command('y')
    #print output

    print "\n>>>> {}".format(datetime.now() - start_time)
    print

if __name__ == "__main__":
    main()
