"""Controls selection of proper class based on the device type."""
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
from netmiko.brocade import BrocadeNosSSH
from netmiko.brocade import BrocadeNetironSSH
from netmiko.brocade import BrocadeFastironSSH
from netmiko.fortinet import FortinetSSH
from netmiko.a10 import A10SSH
from netmiko.avaya import AvayaVspSSH
from netmiko.avaya import AvayaErsSSH
from netmiko.linux import LinuxSSH
from netmiko.ovs import OvsLinuxSSH
from netmiko.enterasys import EnterasysSSH
from netmiko.extreme import ExtremeSSH
from netmiko.alcatel import AlcatelSrosSSH
from netmiko.dell import DellForce10SSH
from netmiko.paloalto import PaloAltoPanosSSH
from netmiko.quanta import QuantaMeshSSH

# The keys of this dictionary are the supported device_types
CLASS_MAPPER_BASE = {
    'cisco_ios': CiscoIosSSH,
    'cisco_xe': CiscoIosSSH,
    'cisco_asa': CiscoAsaSSH,
    'cisco_nxos': CiscoNxosSSH,
    'cisco_xr': CiscoXrSSH,
    'cisco_wlc': CiscoWlcSSH,
    'arista_eos': AristaSSH,
    'hp_procurve': HPProcurveSSH,
    'hp_comware': HPComwareSSH,
    'huawei': HuaweiSSH,
    'f5_ltm': F5LtmSSH,
    'juniper': JuniperSSH,
    'juniper_junos': JuniperSSH,
    'brocade_vdx': BrocadeNosSSH,
    'brocade_nos': BrocadeNosSSH,
    'brocade_fastiron': BrocadeFastironSSH,
    'brocade_netiron': BrocadeNetironSSH,
    'a10': A10SSH,
    'avaya_vsp': AvayaVspSSH,
    'avaya_ers': AvayaErsSSH,
    'linux': LinuxSSH,
    'ovs_linux': OvsLinuxSSH,
    'enterasys': EnterasysSSH,
    'extreme': ExtremeSSH,
    'alcatel_sros': AlcatelSrosSSH,
    'fortinet': FortinetSSH,
    'dell_force10': DellForce10SSH,
    'paloalto_panos': PaloAltoPanosSSH,
    'quanta_mesh': QuantaMeshSSH,
}

# Also support keys that end in _ssh
new_mapper = {}
for k, v in CLASS_MAPPER_BASE.items():
    new_mapper[k] = v
    alt_key = k + u"_ssh"
    new_mapper[alt_key] = v
CLASS_MAPPER = new_mapper

platforms = list(CLASS_MAPPER.keys())
platforms.sort()
platforms_base = list(CLASS_MAPPER_BASE.keys())
platforms_base.sort()
platforms_str = u"\n".join(platforms_base)
platforms_str = u"\n" + platforms_str


def ConnectHandler(*args, **kwargs):
    """Factory function selects the proper class and creates object based on device_type."""
    if kwargs['device_type'] not in platforms:
        raise ValueError('Unsupported device_type: '
                         'currently supported platforms are: {0}'.format(platforms_str))
    ConnectionClass = ssh_dispatcher(kwargs['device_type'])
    return ConnectionClass(*args, **kwargs)


def ssh_dispatcher(device_type):
    """Select the class to be instantiated based on vendor/platform."""
    return CLASS_MAPPER[device_type]
