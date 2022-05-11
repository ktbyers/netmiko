from __future__ import print_function
from __future__ import unicode_literals

from netmiko.cisco_base_connection import CiscoBaseConnection

class CiscoBsp(CiscoBaseConnection):
    '''
    CiscoBsp is based of CiscoBaseConnection
    '''
    pass

class CiscoBspSSH(CiscoBsp):
    '''
    CiscoBspSSH is based of CiscoBsp -- CiscoBaseConnection
    '''

    pass

class CiscoBspTelnet(CiscoBsp):
    '''
    CiscoBspTelnet is based of CiscoBsp -- CiscoBaseConnection
    '''

    pass
