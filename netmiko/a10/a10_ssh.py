from netmiko.ssh_connection import SSHConnection

class A10SSH(SSHConnection):
   def session_preparation(self):
        '''
        Prepare the session after the connection has been established

        '''

        self.enable()
        self.disable_paging(command="terminal length 0\n")
 	self.set_base_prompt()

