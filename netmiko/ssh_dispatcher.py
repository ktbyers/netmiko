"""Controls selection of proper class based on the device type."""
from __future__ import unicode_literals

from netmiko.a10 import A10SSH
from netmiko.accedian import AccedianSSH
from netmiko.alcatel import AlcatelAosSSH
from netmiko.alcatel import AlcatelSrosSSH
from netmiko.arista import AristaSSH
from netmiko.arista import AristaFileTransfer
from netmiko.aruba import ArubaSSH
from netmiko.avaya import AvayaErsSSH
from netmiko.avaya import AvayaVspSSH
from netmiko.brocade import BrocadeNetironSSH
from netmiko.brocade import BrocadeNetironTelnet
from netmiko.brocade import BrocadeNosSSH
from netmiko.calix import CalixB6SSH
from netmiko.checkpoint import CheckPointGaiaSSH
from netmiko.ciena import CienaSaosSSH
from netmiko.cisco import CiscoAsaSSH, CiscoAsaFileTransfer
from netmiko.cisco import CiscoIosSSH, CiscoIosFileTransfer, CiscoIosTelnet, CiscoIosSerial
from netmiko.cisco import CiscoNxosSSH, CiscoNxosFileTransfer
from netmiko.cisco import CiscoS300SSH
from netmiko.cisco import CiscoTpTcCeSSH
from netmiko.cisco import CiscoWlcSSH
from netmiko.cisco import CiscoXrSSH, CiscoXrFileTransfer
from netmiko.coriant import CoriantSSH
from netmiko.dell import DellForce10SSH
from netmiko.dell import DellPowerConnectSSH
from netmiko.dell import DellPowerConnectTelnet
from netmiko.eltex import EltexSSH
from netmiko.enterasys import EnterasysSSH
from netmiko.extreme import ExtremeSSH
from netmiko.extreme import ExtremeWingSSH
from netmiko.extreme import ExtremeTelnet
from netmiko.f5 import F5LtmSSH
from netmiko.fortinet import FortinetSSH
from netmiko.hp import HPProcurveSSH, HPComwareSSH
from netmiko.huawei import HuaweiSSH, HuaweiVrpv8SSH
from netmiko.juniper import JuniperSSH
from netmiko.juniper import JuniperFileTransfer
from netmiko.linux import LinuxSSH
from netmiko.mellanox import MellanoxSSH
from netmiko.mrv import MrvOptiswitchSSH
from netmiko.netapp import NetAppcDotSSH
from netmiko.ovs import OvsLinuxSSH
from netmiko.paloalto import PaloAltoPanosSSH
from netmiko.pluribus import PluribusSSH
from netmiko.quanta import QuantaMeshSSH
from netmiko.ruckus import RuckusFastironSSH
from netmiko.ruckus import RuckusFastironTelnet
from netmiko.terminal_server import TerminalServerSSH
from netmiko.terminal_server import TerminalServerTelnet
from netmiko.ubiquiti import UbiquitiEdgeSSH
from netmiko.vyos import VyOSSSH


# The keys of this dictionary are the supported device_types
CLASS_MAPPER_BASE = {
    'a10': A10SSH,
    'accedian': AccedianSSH,
    'alcatel_aos': AlcatelAosSSH,
    'alcatel_sros': AlcatelSrosSSH,
    'arista_eos': AristaSSH,
    'aruba_os': ArubaSSH,
    'avaya_ers': AvayaErsSSH,
    'avaya_vsp': AvayaVspSSH,
    'brocade_fastiron': RuckusFastironSSH,
    'brocade_netiron': BrocadeNetironSSH,
    'brocade_nos': BrocadeNosSSH,
    'brocade_vdx': BrocadeNosSSH,
    'brocade_vyos': VyOSSSH,
    'checkpoint_gaia': CheckPointGaiaSSH,
    'calix_b6': CalixB6SSH,
    'ciena_saos': CienaSaosSSH,
    'cisco_asa': CiscoAsaSSH,
    'cisco_ios': CiscoIosSSH,
    'cisco_nxos': CiscoNxosSSH,
    'cisco_s300': CiscoS300SSH,
    'cisco_tp': CiscoTpTcCeSSH,
    'cisco_wlc': CiscoWlcSSH,
    'cisco_xe': CiscoIosSSH,
    'cisco_xr': CiscoXrSSH,
    'coriant': CoriantSSH,
    'dell_force10': DellForce10SSH,
    'dell_powerconnect': DellPowerConnectSSH,
    'eltex': EltexSSH,
    'enterasys': EnterasysSSH,
    'extreme': ExtremeSSH,
    'extreme_wing': ExtremeWingSSH,
    'f5_ltm': F5LtmSSH,
    'fortinet': FortinetSSH,
    'generic_termserver': TerminalServerSSH,
    'hp_comware': HPComwareSSH,
    'hp_procurve': HPProcurveSSH,
    'huawei': HuaweiSSH,
    'huawei_vrpv8': HuaweiVrpv8SSH,
    'juniper': JuniperSSH,
    'juniper_junos': JuniperSSH,
    'linux': LinuxSSH,
    'mellanox': MellanoxSSH,
    'mrv_optiswitch': MrvOptiswitchSSH,
    'netapp_cdot': NetAppcDotSSH,
    'ovs_linux': OvsLinuxSSH,
    'paloalto_panos': PaloAltoPanosSSH,
    'pluribus': PluribusSSH,
    'quanta_mesh': QuantaMeshSSH,
    'ruckus_fastiron': RuckusFastironSSH,
    'ubiquiti_edge': UbiquitiEdgeSSH,
    'ubiquiti_edgeswitch': UbiquitiEdgeSSH,
    'vyatta_vyos': VyOSSSH,
    'vyos': VyOSSSH,
}

FILE_TRANSFER_MAP = {
    'arista_eos': AristaFileTransfer,
    'cisco_asa': CiscoAsaFileTransfer,
    'cisco_ios': CiscoIosFileTransfer,
    'cisco_nxos': CiscoNxosFileTransfer,
    'cisco_xe': CiscoIosFileTransfer,
    'cisco_xr': CiscoXrFileTransfer,
    'juniper_junos': JuniperFileTransfer,
}

# Also support keys that end in _ssh
new_mapper = {}
for k, v in CLASS_MAPPER_BASE.items():
    new_mapper[k] = v
    alt_key = k + u"_ssh"
    new_mapper[alt_key] = v
CLASS_MAPPER = new_mapper

new_mapper = {}
for k, v in FILE_TRANSFER_MAP.items():
    new_mapper[k] = v
    alt_key = k + u"_ssh"
    new_mapper[alt_key] = v
FILE_TRANSFER_MAP = new_mapper

# Add telnet drivers
CLASS_MAPPER['brocade_fastiron_telnet'] = RuckusFastironTelnet
CLASS_MAPPER['brocade_netiron_telnet'] = BrocadeNetironTelnet
CLASS_MAPPER['cisco_ios_telnet'] = CiscoIosTelnet
CLASS_MAPPER['dell_powerconnect_telnet'] = DellPowerConnectTelnet
CLASS_MAPPER['generic_termserver_telnet'] = TerminalServerTelnet
CLASS_MAPPER['extreme_telnet'] = ExtremeTelnet
CLASS_MAPPER['ruckus_fastiron_telnet'] = RuckusFastironTelnet

# Add serial drivers
CLASS_MAPPER['cisco_ios_serial'] = CiscoIosSerial

# Add general terminal_server driver and autodetect
CLASS_MAPPER['terminal_server'] = TerminalServerSSH
CLASS_MAPPER['autodetect'] = TerminalServerSSH

platforms = list(CLASS_MAPPER.keys())
platforms.sort()
platforms_base = list(CLASS_MAPPER_BASE.keys())
platforms_base.sort()
platforms_str = "\n".join(platforms_base)
platforms_str = "\n" + platforms_str

scp_platforms = list(FILE_TRANSFER_MAP.keys())
scp_platforms.sort()
scp_platforms_str = "\n".join(scp_platforms)
scp_platforms_str = "\n" + scp_platforms_str


def ConnectHandler(*args, **kwargs):
    """Factory function selects the proper class and creates object based on device_type."""
    if kwargs['device_type'] not in platforms:
        raise ValueError('Unsupported device_type: '
                         'currently supported platforms are: {}'.format(platforms_str))
    ConnectionClass = ssh_dispatcher(kwargs['device_type'])
    return ConnectionClass(*args, **kwargs)


def ssh_dispatcher(device_type):
    """Select the class to be instantiated based on vendor/platform."""
    return CLASS_MAPPER[device_type]


def redispatch(obj, device_type, session_prep=True):
    """Dynamically change Netmiko object's class to proper class.

    Generally used with terminal_server device_type when you need to redispatch after interacting
    with terminal server.
    """
    new_class = ssh_dispatcher(device_type)
    obj.device_type = device_type
    obj.__class__ = new_class
    if session_prep:
        obj.session_preparation()


def FileTransfer(*args, **kwargs):
    """Factory function selects the proper SCP class and creates object based on device_type."""
    if len(args) >= 1:
        device_type = args[0].device_type
    else:
        device_type = kwargs['ssh_conn'].device_type
    if device_type not in scp_platforms:
        raise ValueError('Unsupported SCP device_type: '
                         'currently supported platforms are: {}'.format(scp_platforms_str))
    FileTransferClass = FILE_TRANSFER_MAP[device_type]
    return FileTransferClass(*args, **kwargs)
