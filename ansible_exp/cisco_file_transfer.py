#!/usr/bin/python
'''
Ansible module to transfer files to Cisco IOS devices.

An enable secret is not supported, the username/password provided must have sufficient access
to write a file to the remote filesystem. The lack of support of enable secret is due to
problems encountered on the SCP connection (I think due to how Cisco's SSH is implemented).
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
        )
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
    output = ssh_conn.send_command("show flash: | inc cisco_logging")

    scp_conn = SCPConn(ssh_conn)
    source_file = module.params['source_file']
    source_md5 = file_md5(source_file)

    dest_file = module.params['dest_file']

    scp_conn.scp_transfer_file(source_file, dest_file)
    scp_conn.close()

    output2 = ssh_conn.send_command("show flash: | inc cisco_logging")
    remote_md5_cmd = "verify /md5 {0}".format(dest_file)
    dest_md5 = ssh_conn.send_command(remote_md5_cmd)
    dest_md5 = process_cisco_md5(dest_md5)

    if source_md5 != dest_md5:
        module.fail_json(msg="File transferred to Cisco device, but MD5 does not match" \
                         " source file")

    module.exit_json(msg="Testing...", changed=True, output=output, source_file=source_file,
                     output2=output2, source_md5=source_md5, dest_md5=dest_md5)


if __name__ == "__main__":
    main()
