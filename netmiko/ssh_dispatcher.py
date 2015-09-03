'''
Controls selection of proper class based on the device type
'''

from __future__ import unicode_literals
from netmiko.cisco import CiscoIosSSH
from netmiko.cisco import CiscoAsaSSH
from netmiko.cisco import CiscoNxosSSH
from netmiko.cisco import CiscoXrSSH
from netmiko.cisco import CiscoWlcSSH
from netmiko.arista import AristaSSH
from netmiko.hp import HPProcurveSSH, HPComwareSSH
from netmiko.huawei import HuaweiSSH
from netmiko.f5 import F5LtmSSH
from netmiko.juniper import JuniperSSH
from netmiko.brocade import BrocadeVdxSSH
from netmiko.a10 import A10SSH
from netmiko.avaya import AvayaVspSSH
from netmiko.avaya import AvayaErsSSH

# The keys of this dictionary are the supported device_types
CLASS_MAPPER = {
    'cisco_ios'     : CiscoIosSSH,
    'cisco_xe'      : CiscoIosSSH,
    'cisco_asa'     : CiscoAsaSSH,
    'cisco_nxos'    : CiscoNxosSSH,
    'cisco_xr'      : CiscoXrSSH,
    'cisco_wlc_ssh' : CiscoWlcSSH,
    'cisco_wlc'     : CiscoWlcSSH,
    'arista_eos'    : AristaSSH,
    'hp_procurve'   : HPProcurveSSH,
    'hp_comware'    : HPComwareSSH,
    'huawei'        : HuaweiSSH,
    'f5_ltm'        : F5LtmSSH,
    'juniper'       : JuniperSSH,
    'brocade_vdx'   : BrocadeVdxSSH,
    'a10'           : A10SSH,	
    'avaya_vsp'     : AvayaVspSSH,
    'avaya_ers'     : AvayaErsSSH,
}

platforms = list(CLASS_MAPPER.keys())
platforms.sort()


def ConnectHandler(*args, **kwargs):
    '''
    Factory function that selects the proper class and instantiates the object based on device_type

    Returns the object
    '''

    ConnectionClass = ssh_dispatcher(kwargs['device_type'])
    return ConnectionClass(*args, **kwargs)


def ssh_dispatcher(device_type):
    '''
    Select the class to be instantiated based on vendor/platform
    '''

    return CLASS_MAPPER[device_type]
