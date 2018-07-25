from __future__ import unicode_literals
from netmiko.cisco_base_connection import CiscoSSHConnection


class ExtremeNetironBase(CiscoSSHConnection):
    def save_config(self, cmd='write memory', confirm=False):
        """Save Config"""
        return super(ExtremeNetironBase, self).save_config(cmd=cmd, confirm=confirm)


class ExtremeNetironSSH(ExtremeNetironBase):
    pass


class ExtremeNetironTelnet(ExtremeNetironBase):
    def __init__(self, *args, **kwargs):
        default_enter = kwargs.get('default_enter')
        kwargs['default_enter'] = '\r\n' if default_enter is None else default_enter
        super(ExtremeNetironTelnet, self).__init__(*args, **kwargs)
