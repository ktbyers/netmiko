from netmiko import ConnectHandler
from getpass import getpass

ip = '10.1.200.242'
pw = getpass()

aruba_os = {
    'device_type': 'aruba_os',
    'ip': ip,
    'username': 'mw6000975',
    'password': pw,
}

net_connect = ConnectHandler(**aruba_os)
output = net_connect.send_command('show version')
print output
