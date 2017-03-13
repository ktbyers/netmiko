# -*- coding: utf-8 -*-
from netmiko.base_connection import BaseConnection

class PluribusSSH(BaseConnection):
    '''Common methods for Pluribus.'''
    def disable_paging(self):
        '''Make sure pagins is disabled.'''
        return super(PluribusSSH, self).disable_paging('pager off')
    def session_preparation(self):
        '''
        Prepare the netmiko session:

        - find the prompt
        - disable paging
        '''
        self.set_base_prompt()
        self.disable_paging()
