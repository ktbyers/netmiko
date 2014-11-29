#!/usr/bin/env python

import unittest

from ssh_connection import SSHConnection
from DEVICE_CREDS import *


class VerifySSHConnection(unittest.TestCase):

    def test_disable_paging(self):
        '''
        Verify paging is disabled by looking for string after when paging would
        normally occur
        '''
        self.assertTrue('Configuration register is' in show_version)

    def test_verify_ssh_connect(self):
        '''
        Verify the connection was established successfully
        '''
        self.assertTrue('Cisco IOS Software' in show_version)

    def test_verify_send_command(self):
        '''
        Verify a command can be sent down the channel successfully
        '''
        self.assertTrue(EXPECTED_RESPONSES['interface_ip'] in show_ip)

    def test_find_prompt(self):
        '''
        Verify the router prompt is detected correctly
        '''
        self.assertEqual(net_connect.router_name, EXPECTED_RESPONSES['router_name'])

    def test_strip_prompt(self):
        '''
        Ensure the router prompt is not in the command output
        '''
        self.assertTrue(EXPECTED_RESPONSES['router_prompt'] not in show_ip)

    def test_strip_command(self):
        '''
        Ensure that the command that was executed does not show up in the 
        command output
        '''
        self.assertTrue(basic_command not in show_ip)

    def test_normalize_linefeeds(self):
        '''
        Ensure no '\r\n' sequences
        '''
        self.assertTrue(not '\r\n' in show_ver_command)
    
    def test_enable_mode(self):
        self.assertEqual(net_connect.router_prompt, EXPECTED_RESPONSES['router_prompt'])
        net_connect.enable()
        self.assertEqual(net_connect.router_prompt, EXPECTED_RESPONSES['router_enable'])
            

if __name__ == "__main__":

    EXPECTED_RESPONSES = {
        'router_name'   : 'pynet-rtr1',
        'router_prompt' : 'pynet-rtr1>',
        'router_enable' : 'pynet-rtr1#',
        'interface_ip'  : '10.220.88.20'
    }

    show_ver_command = 'show version'
    basic_command = 'show ip int brief'

    print "\n"
    print "#" * 80
    net_connect = SSHConnection(**cisco_881)
    show_version = net_connect.send_command(show_ver_command)
    show_ip = net_connect.send_command(basic_command)

    unittest.main()


