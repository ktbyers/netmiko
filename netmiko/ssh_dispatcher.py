from cisco import CiscoIosSSH
from arista import AristaSSH

CLASS_MAPPER = {
    'cisco_ios' : CiscoIosSSH,
#    'cisco_asa' : CiscoASAConn,
    'arista_eos'    : AristaSSH,
}

def ssh_dispatcher(device_type):
    '''
    Select the class to be instantiated based on vendor/platform
    '''

    return CLASS_MAPPER[device_type]
