import netmiko

SSHClass = netmiko.ssh_dispatcher(device_type='cisco_xr')

net_connect = SSHClass(ip = '169.254.254.181', username = 'cisco', 
                password = 'cisco', secret = 'secret')

commands_to_send = ['show ipv4 int br', 'show run', 'show version', 'show inventory']

output = ''.join(net_connect.send_command(cmd, delay_factor=.2) for cmd in commands_to_send)

print output

# config_output = net_connect.send_config_set(['interface loopback 200', 'ipv4 address 22.22.22.22/32'])

# print config_output