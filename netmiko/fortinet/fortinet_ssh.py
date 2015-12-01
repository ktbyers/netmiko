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

        self.disable_paging()
        self.set_base_prompt(pri_prompt_terminator='$')

       

    def disable_paging(self, delay_factor=.5):
        '''
        Disable paging is only available with specific roles so it may fail
        '''
        
        check_command = "get system status\n"
        output = self.send_command(check_command)

        self.allow_disable_global = True
        self.vdoms = False

        # According with http://www.gossamer-threads.com/lists/rancid/users/6729
        if output.find("Virtual domain configuration: enable"):
            self.vdoms = True
            vdom_additional_command = "config global\n"
            output = self.send_command(vdom_additional_command)
            if output.find("Command fail"):
                self.allow_disable_global = False
                self.remote_conn.close()
                self.establish_connection(width=100, height=1000)
            
        if self.allow_disable_global:
            disable_paging_commands = [ "config system console\n", "set output standard\n", "end\n" ]
            outputlist = [ self.send_command(command) for command in disable_paging_commands ] 
            # Some code should be inserted for testing the output of the commands
                

    def cleanup(self):
        '''
        Re-enable paging globally
        '''
        if self.allow_disable_global:
            enable_paging_commands = ["config system console\n", "set output more\n", "end\n" ]
            if self.vdoms:
                enable_paging_commands.insert(0,"config global\n")
            outputlist = [ self.send_command(command) for command in enable_paging_commands ] 
            # Some code should be inserted for testing the output of the commands
    
    def establish_connection(self, sleep_time=3, verbose=True, timeout=8, use_keys=False, width=None, height=None):
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
        if width and height:
            self.remote_conn = self.remote_conn_pre.invoke_shell(term='vt100',width=width,height=height)
        else:
            self.remote_conn = self.remote_conn_pre.invoke_shell()
  
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
