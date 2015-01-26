from netmiko.ssh_connection import SSHConnection

class CiscoIosSSH(SSHConnection):

    def enable(self):
        '''
        Enter enable mode
        '''
        output = self.send_command('enable\n')
        if 'assword' in output:
            output += self.send_command(self.secret)

        if self.check_enable_mode():
            self.clear_buffer()
            return True
        else:
            self.clear_buffer()
            return False

        return None
    
    def exit_enable(self):
        '''
        Exit enable mode
        '''
        output = self.send_command('exit\n')

        if self.check_enable_mode():
            self.clear_buffer()
            return False
        else:
            self.clear_buffer()
            return True
        
    def config_mode(self):
        '''
        Exit config mode
        '''
        output = self.send_command('config terminal\n')

        if self.check_config_mode():
            self.clear_buffer()
            return False
        else:
            self.clear_buffer()
            return True

    def exit_config_mode(self):
        '''
        Exit config mode
        '''
        output = self.send_command('end\n')

        if self.check_config_mode():
            self.clear_buffer()
            return False
        else:
            self.clear_buffer()
            return True
        
    def check_enable_mode(self):
        '''
        Finds the Cisco IOS prompt and checks if the prompt contains the right enable mode characters '#'
        
        '''
        
        self.find_prompt()
        if self.router_prompt[-1] == '#':
            return True
        else:
            return False
        
    def check_config_mode(self):
        '''
        Finds the Cisco IOS prompt and checks if the prompt contains the right config mode characters '(config)#'
        
        '''
        
        self.find_prompt()
        if self.router_prompt[-9:] == '(config)#':
            return True
        else:
            return False
