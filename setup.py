from distutils.core import setup

import netmiko

setup(
    name            = 'netmiko',
    version         = netmiko.__version__,
    url             = 'https://github.com/ktbyers/netmiko',
    license         = 'MIT',
    author          = 'Kirk Byers',
    install_requires = ['paramiko>=1.7.5'],
    description     = 'Multi-vendor library to simplify Paramiko SSH connections to network devices',
    packages        = ['netmiko', 'netmiko/cisco', 'netmiko/arista'],
    )
    
