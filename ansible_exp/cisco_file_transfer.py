#!/usr/bin/python
'''
Ansible module to transfer files to Cisco IOS devices.

An enable secret is not supported, the username/password provided must have sufficient access
to write a file to the remote filesystem. The lack of support of enable secret is due to
problems encountered on the SCP connection (I think due to how Cisco's SSH is implemented).

FIX -- should have an overwrite option?
FIX -- might need to assume the flash: file system
FIX -- hard coded to flash:
'''

import re
import hashlib

from ansible.module_utils.basic import *
from netmiko import ConnectHandler, SCPConn


def file_md5(file_name):
    '''
    Compute MD5 hash of file
    '''
    with open(file_name, "rb") as f:
        file_contents = f.read()
        file_hash = hashlib.md5(file_contents).hexdigest()
    return file_hash


def process_cisco_md5(md5_output, pattern=r"= (.*)"):
    '''
    Process the string coming back from Cisco IOS to retrieve the MD5

    .MD5 of flash:file_name Done!
    verify /md5 (flash:file_name) = 410db2a7015eaa42b1fe71f1bf3d59a2
    '''

    match = re.search(pattern, md5_output)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid output from Cisco IOS MD5 command: {0}".format(md5_output))


class FileTransfer(object):
    '''
    Class to manage SCP file transfer and associated SSH control channel
    '''

    def __init__(self, ssh_conn, source_file, dest_file, file_system="flash:"):

        self.ssh_ctl_chan = ssh_conn

        self.source_file = source_file
        self.source_md5 = file_md5(source_file)
        self.dest_file = dest_file
        self.file_system = file_system


    def open_scp_chan(self):
        '''
        Establish a SCP connection to the remote network device
        '''
        self.scp_conn = SCPConn(self.ssh_ctl_chan)


    def close_scp_chan(self):
        '''
        Close the SCP connection to the remote network device
        '''
        self.scp_conn.close()
        self.scp_conn = None


    def check_file_exists(self, remote_cmd=""):
        '''
        Check if the dest_file exists on the remote file system

        Return a boolean

        FIX: Need to fix file_system handler
        '''

        if not remote_cmd:
            remote_cmd = "dir flash:/{0}".format(self.dest_file)

        remote_out = self.ssh_ctl_chan.send_command(remote_cmd)

        search_string = r"Directory of .*{0}".format(self.dest_file)
        if 'Error opening' in remote_out:
            return False
        elif re.search(search_string, remote_out):
            return True
        else:
            raise ValueError("Unexpected output from check_file_exists")


    def compare_md5(self):
        '''
        Calculate remote MD5 and compare to source MD5

        Return boolean
        '''
        remote_md5_cmd = "verify /md5 {0}".format(self.dest_file)

        dest_md5 = self.ssh_ctl_chan.send_command(remote_md5_cmd)
        dest_md5 = process_cisco_md5(dest_md5)

        if self.source_md5 != dest_md5:
            return False

        return True


    def transfer_file(self):
        '''
        SCP transfer source_file to Cisco IOS device

        Verifies MD5 of file on remote device or generates an exception

        FIX: Need to fix file_system handler
        '''

        self.open_scp_chan()
        self.scp_conn.scp_transfer_file(self.source_file, self.dest_file)
        self.close_scp_chan()


    def verify_file(self):
        '''
        Verify the file has been transferred correctly
        '''
        return self.compare_md5()


def main():
    '''
    Ansible module to transfer files to Cisco IOS devices.
    '''

    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True),
            port=dict(default=22, required=False),
            username=dict(required=True),
            password=dict(required=True),
            source_file=dict(required=True),
            dest_file=dict(required=True),
            dest_file_system=dict(required=False),
        ),
        supports_check_mode=True
    )

    net_device = {
        'device_type': 'cisco_ios',
        'ip': module.params['host'],
        'username': module.params['username'],
        'password': module.params['password'],
        'port': int(module.params['port']),
        'verbose': False,
    }


    ssh_conn = ConnectHandler(**net_device)
    source_file = module.params['source_file']
    dest_file = module.params['dest_file']

    scp_transfer = FileTransfer(ssh_conn, source_file, dest_file)

    check_mode = module.check_mode

    # Check if file already exists and has correct MD5
    if scp_transfer.check_file_exists() and scp_transfer.compare_md5():
        module.exit_json(msg="File exists and has correct MD5", changed=False)

    else:
        if check_mode:
            module.exit_json(msg="Check mode: file would be changed on the remote device",
                             changed=True)
        else:
            scp_transfer.transfer_file()
            if scp_transfer.verify_file():
                module.exit_json(msg="File successfully transferred to remote device",
                                 changed=True)

    if check_mode:
        module.fail_json(msg="Check mode: file transferred to remote device failed", output=output)
    else:
        module.fail_json(msg="File transferred to remote device failed", output=output)


if __name__ == "__main__":
    main()
