"""Controls selection of proper class based on the device type."""
from typing import Any, Type, Optional
from typing import TYPE_CHECKING
from netmiko.exceptions import ConnectionException
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from netmiko.a10 import A10SSH
from netmiko.accedian import AccedianSSH
from netmiko.adtran import AdtranOSSSH, AdtranOSTelnet
from netmiko.alcatel import AlcatelAosSSH
from netmiko.allied_telesis import AlliedTelesisAwplusSSH
from netmiko.arista import AristaSSH, AristaTelnet
from netmiko.arista import AristaFileTransfer
from netmiko.apresia import ApresiaAeosSSH, ApresiaAeosTelnet
from netmiko.aruba import ArubaSSH
from netmiko.audiocode import (
    Audiocode72SSH,
    Audiocode66SSH,
    AudiocodeShellSSH,
    Audiocode72Telnet,
    Audiocode66Telnet,
    AudiocodeShellTelnet,
)
from netmiko.brocade import BrocadeFOSSSH
from netmiko.broadcom import BroadcomIcosSSH
from netmiko.calix import CalixB6SSH, CalixB6Telnet
from netmiko.cdot import CdotCrosSSH
from netmiko.centec import CentecOSSSH, CentecOSTelnet
from netmiko.checkpoint import CheckPointGaiaSSH
from netmiko.ciena import CienaSaosSSH, CienaSaosTelnet, CienaSaosFileTransfer
from netmiko.cisco import CiscoAsaSSH, CiscoAsaFileTransfer
from netmiko.cisco import CiscoFtdSSH
from netmiko.cisco import (
    CiscoIosSSH,
    CiscoIosFileTransfer,
    CiscoIosTelnet,
    CiscoIosSerial,
)
from netmiko.cisco import CiscoNxosSSH, CiscoNxosFileTransfer
from netmiko.cisco import CiscoS300SSH, CiscoS300Telnet
from netmiko.cisco import CiscoTpTcCeSSH
from netmiko.cisco import CiscoViptelaSSH
from netmiko.cisco import CiscoWlcSSH
from netmiko.cisco import CiscoXrSSH, CiscoXrTelnet, CiscoXrFileTransfer
from netmiko.citrix import NetscalerSSH
from netmiko.cloudgenix import CloudGenixIonSSH
from netmiko.coriant import CoriantSSH
from netmiko.dell import DellDNOS6SSH
from netmiko.dell import DellDNOS6Telnet
from netmiko.dell import DellForce10SSH
from netmiko.dell import DellOS10SSH, DellOS10FileTransfer
from netmiko.dell import DellSonicSSH
from netmiko.dell import DellPowerConnectSSH
from netmiko.dell import DellPowerConnectTelnet
from netmiko.dell import DellIsilonSSH
from netmiko.dlink import DlinkDSTelnet, DlinkDSSSH
from netmiko.eltex import EltexSSH, EltexEsrSSH
from netmiko.endace import EndaceSSH
from netmiko.enterasys import EnterasysSSH
from netmiko.ericsson import EricssonIposSSH
from netmiko.extreme import ExtremeErsSSH
from netmiko.extreme import ExtremeExosSSH, ExtremeExosFileTransfer
from netmiko.extreme import ExtremeExosTelnet
from netmiko.extreme import ExtremeNetironSSH
from netmiko.extreme import ExtremeNetironTelnet
from netmiko.extreme import ExtremeNosSSH
from netmiko.extreme import ExtremeSlxSSH
from netmiko.extreme import ExtremeTierraSSH
from netmiko.extreme import ExtremeVspSSH
from netmiko.extreme import ExtremeWingSSH
from netmiko.f5 import F5TmshSSH
from netmiko.f5 import F5LinuxSSH
from netmiko.flexvnf import FlexvnfSSH
from netmiko.fortinet import FortinetSSH
from netmiko.hp import HPProcurveSSH, HPProcurveTelnet, HPComwareSSH, HPComwareTelnet
from netmiko.huawei import HuaweiSSH, HuaweiVrpv8SSH, HuaweiTelnet
from netmiko.huawei import HuaweiSmartAXSSH
from netmiko.ipinfusion import IpInfusionOcNOSSSH, IpInfusionOcNOSTelnet
from netmiko.juniper import JuniperSSH, JuniperTelnet, JuniperScreenOsSSH
from netmiko.juniper import JuniperFileTransfer
from netmiko.keymile import KeymileSSH, KeymileNOSSSH
from netmiko.linux import LinuxSSH, LinuxFileTransfer
from netmiko.mikrotik import MikrotikRouterOsSSH, MikrotikRouterOsFileTransfer
from netmiko.mikrotik import MikrotikSwitchOsSSH
from netmiko.mellanox import MellanoxMlnxosSSH
from netmiko.mrv import MrvLxSSH
from netmiko.mrv import MrvOptiswitchSSH
from netmiko.netapp import NetAppcDotSSH
from netmiko.nokia import (
    NokiaSrosSSH,
    NokiaSrosFileTransfer,
    NokiaSrosTelnet,
    NokiaSrlSSH,
)
from netmiko.netgear import NetgearProSafeSSH
from netmiko.oneaccess import OneaccessOneOSTelnet, OneaccessOneOSSSH
from netmiko.ovs import OvsLinuxSSH
from netmiko.paloalto import PaloAltoPanosSSH
from netmiko.paloalto import PaloAltoPanosTelnet
from netmiko.pluribus import PluribusSSH
from netmiko.quanta import QuantaMeshSSH
from netmiko.rad import RadETXSSH
from netmiko.rad import RadETXTelnet
from netmiko.raisecom import RaisecomRoapSSH
from netmiko.raisecom import RaisecomRoapTelnet
from netmiko.ruckus import RuckusFastironSSH
from netmiko.ruckus import RuckusFastironTelnet
from netmiko.ruijie import RuijieOSSSH, RuijieOSTelnet
from netmiko.sixwind import SixwindOSSSH
from netmiko.sophos import SophosSfosSSH
from netmiko.terminal_server import TerminalServerSSH
from netmiko.terminal_server import TerminalServerTelnet
from netmiko.tplink import TPLinkJetStreamSSH, TPLinkJetStreamTelnet
from netmiko.ubiquiti import UbiquitiEdgeRouterSSH
from netmiko.ubiquiti import UbiquitiEdgeSSH
from netmiko.ubiquiti import UbiquitiUnifiSwitchSSH
from netmiko.vyos import VyOSSSH
from netmiko.watchguard import WatchguardFirewareSSH
from netmiko.yamaha import YamahaSSH
from netmiko.yamaha import YamahaTelnet
from netmiko.zte import ZteZxrosSSH
from netmiko.zte import ZteZxrosTelnet
from netmiko.supermicro import SmciSwitchSmisSSH
from netmiko.supermicro import SmciSwitchSmisTelnet
from netmiko.zyxel import ZyxelSSH

if TYPE_CHECKING:
    from netmiko.base_connection import BaseConnection
    from netmiko.scp_handler import BaseFileTransfer

GenericSSH = TerminalServerSSH
GenericTelnet = TerminalServerTelnet

# The keys of this dictionary are the supported device_types
CLASS_MAPPER_BASE = {
    "a10": A10SSH,
    "accedian": AccedianSSH,
    "adtran_os": AdtranOSSSH,
    "alcatel_aos": AlcatelAosSSH,
    "alcatel_sros": NokiaSrosSSH,
    "allied_telesis_awplus": AlliedTelesisAwplusSSH,
    "apresia_aeos": ApresiaAeosSSH,
    "arista_eos": AristaSSH,
    "aruba_os": ArubaSSH,
    "aruba_osswitch": HPProcurveSSH,
    "aruba_procurve": HPProcurveSSH,
    "audiocode_72": Audiocode72SSH,
    "audiocode_66": Audiocode66SSH,
    "audiocode_shell": AudiocodeShellSSH,
    "avaya_ers": ExtremeErsSSH,
    "avaya_vsp": ExtremeVspSSH,
    "broadcom_icos": BroadcomIcosSSH,
    "brocade_fos": BrocadeFOSSSH,
    "brocade_fastiron": RuckusFastironSSH,
    "brocade_netiron": ExtremeNetironSSH,
    "brocade_nos": ExtremeNosSSH,
    "brocade_vdx": ExtremeNosSSH,
    "brocade_vyos": VyOSSSH,
    "checkpoint_gaia": CheckPointGaiaSSH,
    "calix_b6": CalixB6SSH,
    "cdot_cros": CdotCrosSSH,
    "centec_os": CentecOSSSH,
    "ciena_saos": CienaSaosSSH,
    "cisco_asa": CiscoAsaSSH,
    "cisco_ftd": CiscoFtdSSH,
    "cisco_ios": CiscoIosSSH,
    "cisco_nxos": CiscoNxosSSH,
    "cisco_s300": CiscoS300SSH,
    "cisco_tp": CiscoTpTcCeSSH,
    "cisco_viptela": CiscoViptelaSSH,
    "cisco_wlc": CiscoWlcSSH,
    "cisco_xe": CiscoIosSSH,
    "cisco_xr": CiscoXrSSH,
    "cloudgenix_ion": CloudGenixIonSSH,
    "coriant": CoriantSSH,
    "dell_dnos9": DellForce10SSH,
    "dell_force10": DellForce10SSH,
    "dell_os6": DellDNOS6SSH,
    "dell_os9": DellForce10SSH,
    "dell_os10": DellOS10SSH,
    "dell_sonic": DellSonicSSH,
    "dell_powerconnect": DellPowerConnectSSH,
    "dell_isilon": DellIsilonSSH,
    "dlink_ds": DlinkDSSSH,
    "endace": EndaceSSH,
    "eltex": EltexSSH,
    "eltex_esr": EltexEsrSSH,
    "enterasys": EnterasysSSH,
    "ericsson_ipos": EricssonIposSSH,
    "extreme": ExtremeExosSSH,
    "extreme_ers": ExtremeErsSSH,
    "extreme_exos": ExtremeExosSSH,
    "extreme_netiron": ExtremeNetironSSH,
    "extreme_nos": ExtremeNosSSH,
    "extreme_slx": ExtremeSlxSSH,
    "extreme_tierra": ExtremeTierraSSH,
    "extreme_vdx": ExtremeNosSSH,
    "extreme_vsp": ExtremeVspSSH,
    "extreme_wing": ExtremeWingSSH,
    "f5_ltm": F5TmshSSH,
    "f5_tmsh": F5TmshSSH,
    "f5_linux": F5LinuxSSH,
    "flexvnf": FlexvnfSSH,
    "fortinet": FortinetSSH,
    "generic": GenericSSH,
    "generic_termserver": TerminalServerSSH,
    "hp_comware": HPComwareSSH,
    "hp_procurve": HPProcurveSSH,
    "huawei": HuaweiSSH,
    "huawei_smartax": HuaweiSmartAXSSH,
    "huawei_olt": HuaweiSmartAXSSH,
    "huawei_vrpv8": HuaweiVrpv8SSH,
    "ipinfusion_ocnos": IpInfusionOcNOSSSH,
    "juniper": JuniperSSH,
    "juniper_junos": JuniperSSH,
    "juniper_screenos": JuniperScreenOsSSH,
    "keymile": KeymileSSH,
    "keymile_nos": KeymileNOSSSH,
    "linux": LinuxSSH,
    "mikrotik_routeros": MikrotikRouterOsSSH,
    "mikrotik_switchos": MikrotikSwitchOsSSH,
    "mellanox": MellanoxMlnxosSSH,
    "mellanox_mlnxos": MellanoxMlnxosSSH,
    "mrv_lx": MrvLxSSH,
    "mrv_optiswitch": MrvOptiswitchSSH,
    "netapp_cdot": NetAppcDotSSH,
    "netgear_prosafe": NetgearProSafeSSH,
    "netscaler": NetscalerSSH,
    "nokia_sros": NokiaSrosSSH,
    "nokia_srl": NokiaSrlSSH,
    "oneaccess_oneos": OneaccessOneOSSSH,
    "ovs_linux": OvsLinuxSSH,
    "paloalto_panos": PaloAltoPanosSSH,
    "pluribus": PluribusSSH,
    "quanta_mesh": QuantaMeshSSH,
    "rad_etx": RadETXSSH,
    "raisecom_roap": RaisecomRoapSSH,
    "ruckus_fastiron": RuckusFastironSSH,
    "ruijie_os": RuijieOSSSH,
    "sixwind_os": SixwindOSSSH,
    "sophos_sfos": SophosSfosSSH,
    "supermicro_smis": SmciSwitchSmisSSH,
    "tplink_jetstream": TPLinkJetStreamSSH,
    "ubiquiti_edge": UbiquitiEdgeSSH,
    "ubiquiti_edgerouter": UbiquitiEdgeRouterSSH,
    "ubiquiti_edgeswitch": UbiquitiEdgeSSH,
    "ubiquiti_unifiswitch": UbiquitiUnifiSwitchSSH,
    "vyatta_vyos": VyOSSSH,
    "vyos": VyOSSSH,
    "watchguard_fireware": WatchguardFirewareSSH,
    "zte_zxros": ZteZxrosSSH,
    "yamaha": YamahaSSH,
    "zyxel_os": ZyxelSSH,
}

FILE_TRANSFER_MAP = {
    "arista_eos": AristaFileTransfer,
    "ciena_saos": CienaSaosFileTransfer,
    "cisco_asa": CiscoAsaFileTransfer,
    "cisco_ios": CiscoIosFileTransfer,
    "cisco_nxos": CiscoNxosFileTransfer,
    "cisco_xe": CiscoIosFileTransfer,
    "cisco_xr": CiscoXrFileTransfer,
    "dell_os10": DellOS10FileTransfer,
    "extreme_exos": ExtremeExosFileTransfer,
    "juniper_junos": JuniperFileTransfer,
    "linux": LinuxFileTransfer,
    "nokia_sros": NokiaSrosFileTransfer,
    "mikrotik_routeros": MikrotikRouterOsFileTransfer,
}

# Also support keys that end in _ssh
new_mapper = {}
for k, v in CLASS_MAPPER_BASE.items():
    new_mapper[k] = v
    alt_key = k + "_ssh"
    new_mapper[alt_key] = v
CLASS_MAPPER = new_mapper

new_mapper = {}
for k, v in FILE_TRANSFER_MAP.items():
    new_mapper[k] = v
    alt_key = k + "_ssh"
    new_mapper[alt_key] = v
FILE_TRANSFER_MAP = new_mapper

# Add telnet drivers
CLASS_MAPPER["adtran_os_telnet"] = AdtranOSTelnet
CLASS_MAPPER["apresia_aeos_telnet"] = ApresiaAeosTelnet
CLASS_MAPPER["arista_eos_telnet"] = AristaTelnet
CLASS_MAPPER["aruba_procurve_telnet"] = HPProcurveTelnet
CLASS_MAPPER["audiocode_72_telnet"] = Audiocode72Telnet
CLASS_MAPPER["audiocode_66_telnet"] = Audiocode66Telnet
CLASS_MAPPER["audiocode_shell_telnet"] = AudiocodeShellTelnet
CLASS_MAPPER["brocade_fastiron_telnet"] = RuckusFastironTelnet
CLASS_MAPPER["brocade_netiron_telnet"] = ExtremeNetironTelnet
CLASS_MAPPER["calix_b6_telnet"] = CalixB6Telnet
CLASS_MAPPER["centec_os_telnet"] = CentecOSTelnet
CLASS_MAPPER["ciena_saos_telnet"] = CienaSaosTelnet
CLASS_MAPPER["cisco_ios_telnet"] = CiscoIosTelnet
CLASS_MAPPER["cisco_xr_telnet"] = CiscoXrTelnet
CLASS_MAPPER["cisco_s300_telnet"] = CiscoS300Telnet
CLASS_MAPPER["dell_dnos6_telnet"] = DellDNOS6Telnet
CLASS_MAPPER["dell_powerconnect_telnet"] = DellPowerConnectTelnet
CLASS_MAPPER["dlink_ds_telnet"] = DlinkDSTelnet
CLASS_MAPPER["extreme_telnet"] = ExtremeExosTelnet
CLASS_MAPPER["extreme_exos_telnet"] = ExtremeExosTelnet
CLASS_MAPPER["extreme_netiron_telnet"] = ExtremeNetironTelnet
CLASS_MAPPER["generic_telnet"] = GenericTelnet
CLASS_MAPPER["generic_termserver_telnet"] = TerminalServerTelnet
CLASS_MAPPER["hp_procurve_telnet"] = HPProcurveTelnet
CLASS_MAPPER["hp_comware_telnet"] = HPComwareTelnet
CLASS_MAPPER["huawei_telnet"] = HuaweiTelnet
CLASS_MAPPER["huawei_olt_telnet"] = HuaweiSmartAXSSH
CLASS_MAPPER["ipinfusion_ocnos_telnet"] = IpInfusionOcNOSTelnet
CLASS_MAPPER["juniper_junos_telnet"] = JuniperTelnet
CLASS_MAPPER["nokia_sros_telnet"] = NokiaSrosTelnet
CLASS_MAPPER["oneaccess_oneos_telnet"] = OneaccessOneOSTelnet
CLASS_MAPPER["paloalto_panos_telnet"] = PaloAltoPanosTelnet
CLASS_MAPPER["rad_etx_telnet"] = RadETXTelnet
CLASS_MAPPER["raisecom_telnet"] = RaisecomRoapTelnet
CLASS_MAPPER["ruckus_fastiron_telnet"] = RuckusFastironTelnet
CLASS_MAPPER["ruijie_os_telnet"] = RuijieOSTelnet
CLASS_MAPPER["supermicro_smis_telnet"] = SmciSwitchSmisTelnet
CLASS_MAPPER["tplink_jetstream_telnet"] = TPLinkJetStreamTelnet
CLASS_MAPPER["yamaha_telnet"] = YamahaTelnet
CLASS_MAPPER["zte_zxros_telnet"] = ZteZxrosTelnet

# Add serial drivers
CLASS_MAPPER["cisco_ios_serial"] = CiscoIosSerial

# Add general terminal_server driver and autodetect
CLASS_MAPPER["terminal_server"] = TerminalServerSSH
CLASS_MAPPER["autodetect"] = TerminalServerSSH

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

telnet_platforms = [x for x in platforms if "telnet" in x]
telnet_platforms_str = "\n".join(telnet_platforms)
telnet_platforms_str = "\n" + telnet_platforms_str


def ConnectHandler(*args: Any, **kwargs: Any) -> "BaseConnection":
    """Factory function selects the proper class and creates object based on device_type."""
    device_type = kwargs["device_type"]
    if device_type not in platforms:
        if device_type is None:
            msg_str = platforms_str
        else:
            msg_str = telnet_platforms_str if "telnet" in device_type else platforms_str
        raise ValueError(
            "Unsupported 'device_type' "
            "currently supported platforms are: {}".format(msg_str)
        )
    ConnectionClass = ssh_dispatcher(device_type)
    return ConnectionClass(*args, **kwargs)


def ConnLogOnly(
    log_file: str = "netmiko.log",
    log_level: Optional[int] = None,
    log_format: Optional[str] = None,
    **kwargs: Any,
) -> Optional["BaseConnection"]:
    """
    Dispatcher function that will return either: netmiko_object or None

    Excluding errors in logging configuration should never generate an exception
    all errors should be logged.
    """

    import logging

    if log_level is None:
        log_level = logging.ERROR
    if log_format is None:
        log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"

    logging.basicConfig(filename=log_file, level=log_level, format=log_format)
    logger = logging.getLogger(__name__)

    try:
        kwargs["auto_connect"] = False
        net_connect = ConnectHandler(**kwargs)
        hostname = net_connect.host
        port = net_connect.port
        device_type = net_connect.device_type

        net_connect._open()
        msg = f"Netmiko connection succesful to {hostname}:{port}"
        logger.info(msg)
        return net_connect
    except NetmikoAuthenticationException as e:
        msg = (
            f"Authentication failure to: {hostname}:{port} ({device_type})\n\n{str(e)}"
        )
        logger.error(msg)
        return None
    except NetmikoTimeoutException as e:
        if "DNS failure" in str(e):
            msg = f"Device failed due to a DNS failure, hostname {hostname}"
        elif "TCP connection to device failed" in str(e):
            msg = f"Netmiko was unable to reach the provided host and port: {hostname}:{port}"
            msg += f"\n\n{str(e)}"
        logger.error(msg)
        return None
    except Exception as e:
        msg = f"An unknown exception occurred during connection:\n\n{str(e)}"
        logger.error(msg)
        return None


def ConnUnify(
    **kwargs: Any,
) -> "BaseConnection":

    try:
        kwargs["auto_connect"] = False
        net_connect = ConnectHandler(**kwargs)
        hostname = net_connect.host
        port = net_connect.port
        device_type = net_connect.device_type
        general_msg = f"Connection failure to {hostname}:{port} ({device_type})\n\n"

        net_connect._open()
        return net_connect
    except NetmikoAuthenticationException as e:
        msg = general_msg + str(e)
        raise ConnectionException(msg)
    except NetmikoTimeoutException as e:
        msg = general_msg + str(e)
        raise ConnectionException(msg)
    except Exception as e:
        msg = f"An unknown exception occurred during connection:\n\n{str(e)}"
        raise ConnectionException(msg)


def ssh_dispatcher(device_type: str) -> Type["BaseConnection"]:
    """Select the class to be instantiated based on vendor/platform."""
    return CLASS_MAPPER[device_type]


def redispatch(
    obj: "BaseConnection", device_type: str, session_prep: bool = True
) -> None:
    """Dynamically change Netmiko object's class to proper class.
    Generally used with terminal_server device_type when you need to redispatch after interacting
    with terminal server.
    """
    new_class = ssh_dispatcher(device_type)
    obj.device_type = device_type
    obj.__class__ = new_class
    if session_prep:
        obj._try_session_preparation()


def FileTransfer(*args: Any, **kwargs: Any) -> "BaseFileTransfer":
    """Factory function selects the proper SCP class and creates object based on device_type."""
    if len(args) >= 1:
        device_type = args[0].device_type
    else:
        device_type = kwargs["ssh_conn"].device_type
    if device_type not in scp_platforms:
        raise ValueError(
            "Unsupported SCP device_type: "
            "currently supported platforms are: {}".format(scp_platforms_str)
        )
    FileTransferClass: Type["BaseFileTransfer"]
    FileTransferClass = FILE_TRANSFER_MAP[device_type]
    return FileTransferClass(*args, **kwargs)
