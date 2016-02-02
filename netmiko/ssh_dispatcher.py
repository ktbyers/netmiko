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
from netmiko.fortinet import FortinetSSH
from netmiko.a10 import A10SSH
from netmiko.avaya import AvayaVspSSH
from netmiko.avaya import AvayaErsSSH
from netmiko.ovs import OvsLinuxSSH
from netmiko.enterasys import EnterasysSSH
from netmiko.extreme import ExtremeSSH
from netmiko.alcatel import AlcatelSrosSSH
from netmiko.dell import DellForce10SSH

# The keys of this dictionary are the supported device_types
CLASS_MAPPER = {
    'cisco_ios': CiscoIosSSH,
    'cisco_xe': CiscoIosSSH,
    'cisco_asa': CiscoAsaSSH,
    'cisco_nxos': CiscoNxosSSH,
    'cisco_xr': CiscoXrSSH,
    'cisco_wlc_ssh': CiscoWlcSSH,
    'cisco_wlc': CiscoWlcSSH,
    'arista_eos': AristaSSH,
    'hp_procurve': HPProcurveSSH,
    'hp_comware': HPComwareSSH,
    'huawei': HuaweiSSH,
    'f5_ltm': F5LtmSSH,
    'juniper': JuniperSSH,
    'brocade_vdx': BrocadeVdxSSH,
    'a10': A10SSH,
    'avaya_vsp': AvayaVspSSH,
    'avaya_ers': AvayaErsSSH,
    'ovs_linux': OvsLinuxSSH,
    'enterasys': EnterasysSSH,
    'extreme': ExtremeSSH,
    'alcatel_sros': AlcatelSrosSSH,
    'fortinet': FortinetSSH,
    'dell_force10': DellForce10SSH,
    'cisco_ios_ssh': CiscoIosSSH,
    'cisco_xe_ssh': CiscoIosSSH,
    'cisco_asa_ssh': CiscoAsaSSH,
    'cisco_nxos_ssh': CiscoNxosSSH,
    'cisco_xr_ssh': CiscoXrSSH,
    'cisco_wlc_ssh': CiscoWlcSSH,
    'arista_eos_ssh': AristaSSH,
    'hp_procurve_ssh': HPProcurveSSH,
    'hp_comware_ssh': HPComwareSSH,
    'huawei_ssh': HuaweiSSH,
    'f5_ltm_ssh': F5LtmSSH,
    'juniper_ssh': JuniperSSH,
    'brocade_vdx_ssh': BrocadeVdxSSH,
    'a10_ssh': A10SSH,
    'avaya_vsp_ssh': AvayaVspSSH,
    'avaya_ers_ssh': AvayaErsSSH,
    'ovs_linux_ssh': OvsLinuxSSH,
    'enterasys_ssh': EnterasysSSH,
    'extreme_ssh': ExtremeSSH,
    'alcatel_sros_ssh': AlcatelSrosSSH,
    'fortinet_ssh': FortinetSSH,
    'dell_force10_ssh': DellForce10SSH,
}

platforms = list(CLASS_MAPPER.keys())
platforms.sort()
platforms_str = u"\n".join(platforms)
platforms_str = u"\n" + platforms_str


def ConnectHandler(*args, **kwargs):
    '''
    Factory function that selects the proper class and instantiates the object based on device_type

    Returns the object
    '''

    if kwargs['device_type'] not in platforms:
        raise ValueError('Unsupported device_type: '
                         'currently supported platforms are: {0}'.format(platforms_str))
    ConnectionClass = ssh_dispatcher(kwargs['device_type'])
    return ConnectionClass(*args, **kwargs)


def ssh_dispatcher(device_type):
    '''
    Select the class to be instantiated based on vendor/platform
    '''
    return CLASS_MAPPER[device_type]
