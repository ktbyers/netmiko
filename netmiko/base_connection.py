import paramiko
import time
import socket

from netmiko_globals import MAX_BUFFER
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException


class BaseSSHConnection(object):
    '''
    Defines vendor independent methods.

    Otherwise method left as a stub method.
    '''

    def __init__(self, ip, username, password, secret='', port=22, device_type='', verbose=True):

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.secret = secret
        self.device_type = device_type

        if not verbose:
            self.establish_connection(verbose=False)
        else:
            self.establish_connection()
        self.disable_paging()
        self.find_prompt()


    def establish_connection(self, sleep_time=3, verbose=True, timeout=8):
        '''
        Establish SSH connection to the network device

        Timeout will generate a NetMikoTimeoutException
        Authentication failure will generate a NetMikoAuthenticationException
        '''

        # Create instance of SSHClient object
        self.remote_conn_pre = paramiko.SSHClient()

        # Automatically add untrusted hosts (make sure appropriate for your environment)
        self.remote_conn_pre.set_missing_host_key_policy(
             paramiko.AutoAddPolicy())

        # initiate SSH connection
        if verbose: print "SSH connection established to {0}:{1}".format(self.ip, self.port)

        try:
            self.remote_conn_pre.connect(hostname=self.ip, port=self.port, 
                        username=self.username, password=self.password,
                        look_for_keys=False, timeout=timeout)
        except socket.error as e:
            msg = "Connection to device timed-out: {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            raise NetMikoTimeoutException(msg)
        except paramiko.ssh_exception.AuthenticationException as e:
            msg = "Authentication failure: unable to connect to device {device_type} {ip}:{port}".format(
                device_type=self.device_type, ip=self.ip, port=self.port)
            msg += '\n' + str(e)
            raise NetMikoAuthenticationException(msg)

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre.invoke_shell()
        if verbose: print "Interactive SSH session established"

        # Strip the initial router prompt
        time.sleep(sleep_time)
        output = self.remote_conn.recv(MAX_BUFFER)


    def disable_paging(self):
        pass


    def find_prompt(self):
        pass    


    def clear_buffer(self):
        '''
        Read any data available in the channel 
        '''

        if self.remote_conn.recv_ready():
            return self.remote_conn.recv(MAX_BUFFER)
        else:
            return None

    
    def send_command(self, command_string, delay_factor=1, max_loops=30, 
                                    strip_prompt=True, strip_command=True):
        pass


    def strip_prompt(self, a_string):
        '''
        Strip the trailing router prompt from the output
        '''

        response_list = a_string.split('\n')
        if response_list[-1].strip() == self.router_prompt:
            return '\n'.join(response_list[:-1])
        else:
            return a_string


    def strip_command(self, command_string, output):
        '''
        Strip command_string from output string
        '''

        command_length = len(command_string)
        return output[command_length:]


    def normalize_linefeeds(self, a_string):
        '''
        Convert '\r\n' to '\n'
        '''

        return a_string.replace('\r\n', '\n')


    def enable(self):
        pass


    def config_mode(self):
        pass


    def exit_config_mode(self):
        pass


    def send_config_set(self, config_commands=None):
        pass


    def strip_ansi_escape_codes(self, string_buffer):
        '''
        Not needed in the general case (just return unmodified)

        HP ProCurve requires ansi escape codes to be stripped
        '''
        return string_buffer 

    
    def cleanup(self):
        '''
        Any needed cleanup before closing connection
        '''
        pass


    def disconnect(self):
        '''
        Gracefully close the SSH connection
        '''

        self.cleanup()
        self.remote_conn_pre.close()


    def commit(self):
        '''
        Commit method for platforms that support this
        '''

        pass
