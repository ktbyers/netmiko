# -*- coding: utf-8 -*-
from netmiko.base_connection import BaseConnection


class PluribusSSH(BaseConnection):
    '''Common methods for Pluribus.'''

    def __init__(self, *args, **kwargs):
        super(PluribusSSH, self).__init__(*args, **kwargs)
        self.__config_mode = False

    def disable_paging(self):
        '''Make sure paging is disabled.'''
        return super(PluribusSSH, self).disable_paging('pager off')

    def session_preparation(self):
        '''
        Prepare the netmiko session:

        - find the prompt
        - disable paging
        '''
        self.set_base_prompt()
        self.disable_paging()

    def check_config_mode(self):
        '''
        Pluribus devices don't have a special config mode.
        Therefore it can be considered as always in config mode.
        '''
        return self.__config_mode

    def config_mode(self):
        '''
        No special actions to enter in config mode.
        '''
        self.__config_mode = True
        return ''

    def exit_config_mode(self):
        '''
        No special actions to exit config mode.
        '''
        self.__config_mode = False
        return ''
