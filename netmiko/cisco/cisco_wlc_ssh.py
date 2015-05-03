from __future__ import print_function

import time

from netmiko.ssh_connection import BaseSSHConnection
from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException

class CiscoWlcSSH(BaseSSHConnection):

    def establish_connection(self, sleep_time=3, verbose=True, timeout=8, use_keys=False):
        '''
        Establish SSH connection to the network device

        Timeout will generate a NetmikoTimeoutException
        Authentication failure will generate a NetmikoAuthenticationException

        WLC presents with the following on login

        login as: user

        (Cisco Controller)

        User: user

        Password:****
       
        Manually send username/password to work around this. 
        '''

        # Create instance of SSHClient object
        self.remote_conn_pre = paramiko.SSHClient()

        # Automatically add untrusted hosts (make sure appropriate for your environment)
        self.remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # initiate SSH connection
        if verbose:
            print("SSH connection established to {0}:{1}".format(self.ip, self.port))

        try:
            self.remote_conn_pre.connect(hostname=self.ip, port=self.port,
                                         username=self.username, password=self.password,
                                         look_for_keys=use_keys, allow_agent=False,
                                         timeout=timeout)
        except socket.error as e:
            msg = "Connection to device timed-out: {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            raise NetMikoTimeoutException(msg)
        except paramiko.ssh_exception.AuthenticationException as e:
            msg = "Authentication failure: unable to connect {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            msg += '\n' + str(e)
            raise NetMikoAuthenticationException(msg)

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre.invoke_shell()

        # Handle WLCs extra
        self.remote_conn.send(self.username + '\n')
        time.sleep(.2)
        self.remote_conn.send(self.password + '\n')
        if verbose: 
            print("Interactive SSH session established")

        # Strip the initial router prompt
        time.sleep(sleep_time)
        return self.remote_conn.recv(MAX_BUFFER)


    def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        Cisco WLC uses "config paging disable" to disable paging
        '''

        self.disable_paging(command="config paging disable\n")
        self.set_base_prompt()


    def cleanup(self):
        '''
        Reset WLC back to normal paging
        '''

        self.send_command("config paging enable\n")

