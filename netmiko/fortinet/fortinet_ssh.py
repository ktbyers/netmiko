from netmiko.ssh_connection import SSHConnection
import paramiko
import time
import socket
import re
import io

from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException

class FortinetSSH(SSHConnection):

    def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        Disable paging
        Change base prompt
        '''

        self.set_base_prompt(pri_prompt_terminator='$')

    def establish_connection(self, sleep_time=3, verbose=True, timeout=8, use_keys=False):
        '''
        Establish SSH connection to the network device
        Timeout will generate a NetMikoTimeoutException
        Authentication failure will generate a NetMikoAuthenticationException
        use_keys is a boolean that allows ssh-keys to be used for authentication
        '''

        # Create instance of SSHClient object
        self.remote_conn_pre = paramiko.SSHClient()

        # Automatically add untrusted hosts (make sure appropriate for your environment)
        self.remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # initiate SSH connection
        try:
            self.remote_conn_pre.connect(hostname=self.ip, port=self.port,
                                         username=self.username, password=self.password,
                                         look_for_keys=use_keys, allow_agent=False,
                                         timeout=timeout)
        except socket.error:
            msg = "Connection to device timed-out: {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            raise NetMikoTimeoutException(msg)
        except paramiko.ssh_exception.AuthenticationException as auth_err:
            msg = "Authentication failure: unable to connect {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            msg += '\n' + str(auth_err)
            raise NetMikoAuthenticationException(msg)

        if verbose:
            print("SSH connection established to {0}:{1}".format(self.ip, self.port))

        # Since Fortinet paging setting is global we need a way to disable paging 
        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre.invoke_shell(term='vt100',width=100,height=1000)
        if verbose:
            print("Interactive SSH session established")

        # Strip the initial router prompt
        time.sleep(sleep_time)
        return self.remote_conn.recv(MAX_BUFFER).decode('utf-8')

    def config_mode(self, config_command=''):
       '''
       No config mode for Fortinet devices
       '''
       return u''

    def exit_config_mode(self, exit_config=''):
       '''
       No config mode for Fortinet devices
       '''
       return u''
