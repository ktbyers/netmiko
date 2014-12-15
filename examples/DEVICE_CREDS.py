cisco_881 = {
    'device_type': 'cisco_ios',
    'ip':   '10.10.10.227',
    'username': 'test1',
    'password': 'password',
    'secret': 'secret',
    'verbose': False,
}

cisco_asa = {
    'device_type': 'cisco_asa',
    'ip':   '10.10.10.226',
    'username': 'admin',
    'password': 'password',
    'secret': 'secret',
    'verbose': False,
}

arista_veos_sw1 = {
    'device_type': 'arista_eos',
    'ip':   '10.10.10.227',
    'username': 'admin1',
    'password': 'password',
    'secret': '',
    'port': 8222,
    'verbose': False,
}
arista_veos_sw2 = {
    'device_type': 'arista_eos',
    'ip':   '10.10.10.227',
    'username': 'admin1',
    'password': 'password',
    'secret': '',
    'port': 8322,
    'verbose': False,
}
arista_veos_sw3 = {
    'device_type': 'arista_eos',
    'ip':   '10.10.10.227',
    'username': 'admin1',
    'password': 'password',
    'secret': '',
    'port': 8422,
    'verbose': False,
}

arista_veos_sw4 = {
    'device_type': 'arista_eos',
    'ip':   '10.10.10.227',
    'username': 'admin1',
    'password': 'password',
    'secret': '',
    'port': 8522,
    'verbose': False,
}

hp_procurve = {
    'device_type': 'hp_procurve',
    'ip':   '10.10.10.227',
    'username': 'admin',
    'password': 'password',
    'secret': '',
    'port': 9922,
    'verbose': False,
}

f5_ltm = {
    'device_type': 'hp_procurve',
    'ip':   '10.10.10.227',
    'username': 'admin',
    'password': 'password',
    'secret': '',
    'port': 22,
    'verbose': False,  
}    
    
all_devices = [
    cisco_881,
    cisco_asa,
    arista_veos_sw1,
    arista_veos_sw2,
    arista_veos_sw3,
    arista_veos_sw4,
    hp_procurve
    f5_ltm    
]
