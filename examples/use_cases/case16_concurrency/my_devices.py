from getpass import getpass

std_pwd = getpass("Enter standard password: ")

pynet_rtr1 = {
    'device_type': 'cisco_ios',
    'ip': '184.105.247.70',
    'username': 'pyclass',
    'password': std_pwd,
}

pynet_rtr2 = {
    'device_type': 'cisco_ios',
    'ip': '184.105.247.71',
    'username': 'pyclass',
    'password': std_pwd,
}

pynet_sw1 = {
    'device_type': 'arista_eos',
    'ip': '184.105.247.72',
    'username': 'pyclass',
    'password': std_pwd,
}

pynet_sw2 = {
    'device_type': 'arista_eos',
    'ip': '184.105.247.73',
    'username': 'pyclass',
    'password': std_pwd,
}

pynet_sw3 = {
    'device_type': 'arista_eos',
    'ip': '184.105.247.74',
    'username': 'pyclass',
    'password': std_pwd,
}

pynet_sw4 = {
    'device_type': 'arista_eos',
    'ip': '184.105.247.75',
    'username': 'pyclass',
    'password': std_pwd,
}

juniper_srx = {
    'device_type': 'juniper_junos',
    'ip': '184.105.247.76',
    'username': 'pyclass',
    'password': std_pwd,
}

device_list = [
        pynet_rtr1,
        pynet_rtr2,
        pynet_sw1,
        pynet_sw2,
        pynet_sw3,
        pynet_sw4,
        juniper_srx,
]
