from __future__ import unicode_literals
from netmiko.ssh_connection import SSHConnection
import re


class CiscoNxosSSH(SSHConnection):

    @staticmethod
    def normalize_linefeeds(a_string):
        '''
        Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text
        '''

        newline = re.compile(r'(\r\r\n|\r\n)')

        return newline.sub('\n', a_string).replace('\r', '')
