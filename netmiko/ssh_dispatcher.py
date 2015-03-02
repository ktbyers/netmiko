from cisco import CiscoIosSSH
from cisco import CiscoAsaSSH
from cisco import CiscoNxosSSH
from cisco import CiscoXrSSH
from arista import AristaSSH
from hp import HPProcurveSSH, HPComwareSSH
from f5 import F5LtmSSH
from juniper import JuniperSSH
from brocade import BrocadeVdxSSH

# The keys of this dictionary are the supported device_types
CLASS_MAPPER = {
    'cisco_ios'     : CiscoIosSSH,
    'cisco_xe'      : CiscoIosSSH,
    'cisco_asa'     : CiscoAsaSSH,
    'cisco_nxos'    : CiscoNxosSSH,
    'cisco_xr'      : CiscoXrSSH,
    'arista_eos'    : AristaSSH,
    'hp_procurve'   : HPProcurveSSH,
    'hp_comware'    : HPComwareSSH,
    'f5_ltm'        : F5LtmSSH,
    'juniper'       : JuniperSSH,
    'brocade_vdx'   : BrocadeVdxSSH,
}

def ssh_dispatcher(device_type):
    '''
    Select the class to be instantiated based on vendor/platform
    '''

    return CLASS_MAPPER[device_type]
