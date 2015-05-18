#!/usr/bin/python
'''
Ansible module to perform config merge on Cisco IOS devices.

This module presupposes that the relevant file has been transferred to the device

The module is not idempotent and does not support check_mode
'''

from ansible.module_utils.basic import *
from netmiko import ConnectHandler

def main():
    '''
    Ansible module to perform config merge on Cisco IOS devices.
    '''

    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True),
            port=dict(default=22, required=False),
            username=dict(required=True),
            password=dict(required=True),
            merge_file=dict(required=True),
            dest_file_system=dict(default='flash:', required=False),
        ),
        supports_check_mode=False
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
    ssh_conn.enable()
    merge_file = module.params['merge_file']
    dest_file_system = module.params['dest_file_system']

    # Disable file copy confirmation
    ssh_conn.send_config_set(['file prompt quiet'])

    # Perform config merge
    cmd = "copy {0}{1} running-config".format(dest_file_system, merge_file)
    output = ssh_conn.send_command(cmd)

    # Enable file copy confirmation
    ssh_conn.send_config_set(['file prompt alert'])

    if ' bytes copied in ' in output:
        module.exit_json(msg="File merged on remote device",
                         changed=True)
    else:
        module.fail_json(msg="Unexpected failure during attempted config merge. "
                             "Please verify the current configuration on the network device.")


if __name__ == "__main__":
    main()
