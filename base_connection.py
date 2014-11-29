import paramiko
import time

from netmiko_globals import MAX_BUFFER


class BaseSSHConnection(object):
    '''
    Defines vendor independent methods.

    Otherwise method left as a stub method.
    '''

    def __init__(self, ip, username, password, port=22):

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

        self.establish_connection()
        self.disable_paging()
        self.find_prompt()


    def establish_connection(self, sleep_time=3):
        '''
        Establish SSH connection to the network device
        '''

        # Create instance of SSHClient object
        self.remote_conn_pre = paramiko.SSHClient()

        # Automatically add untrusted hosts (make sure appropriate for your environment)
        self.remote_conn_pre.set_missing_host_key_policy(
             paramiko.AutoAddPolicy())

        # initiate SSH connection
        print "SSH connection established to {0}:{1}".format(self.ip, self.port)
        self.remote_conn_pre.connect(hostname=self.ip, port=self.port, 
                        username=self.username, password=self.password)

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre.invoke_shell()
        print "Interactive SSH session established"

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

    
    def send_command(self, command_string, delay_factor=1, max_loops=30):
        pass


    def strip_prompt(self, a_string):
        '''
        Strip the trailing router prompt from the output
        '''

        response_list = a_string.split('\n')
        if response_list[-1] == self.router_prompt:
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


    def enable_mode(self):
        pass


    def config_mode(self):
        pass

