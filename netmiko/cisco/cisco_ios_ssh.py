from netmiko.ssh_connection import SSHConnection

class CiscoIosSSH(SSHConnection):

    def enable_mode(self):
        '''
        Enter enable mode
        '''
        
        DEBUG = False
        
        if self.check_enable_mode():
            return True
        
        output = self.send_command('enable\n')
        
        if 'assword' in output:
            output += self.send_command(self.secret)

        if DEBUG: print output

        if self.check_enable_mode():
            return True
        else:
            return False

        return None
        
    def exit_enable_mode(self):
        '''
        Exit enable mode
        '''
        
        DEBUG = False
        
        if not self.check_enable_mode():
            return True
        
        output = self.send_command('exit\n')

        if DEBUG: print output

        if self.check_enable_mode():
            return False
        else:
            return True
    
        
    def config_mode(self):
        '''
        Exit config mode
        '''
        
        DEBUG = False
        
        if self.check_config_mode():
            return True
        
        output = self.send_command('configure terminal\n')

        if DEBUG: print output
        
        if self.check_config_mode():
            return True
        else:
            return False

    def exit_config_mode(self):
        '''
        Exit config mode
        '''
        
        DEBUG = False
        
        if not self.check_config_mode():
            return True
        
        output = self.send_command('end\n')
        
        if DEBUG: print output
        
        if self.check_config_mode():
            return False
        else:
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
        if self.router_prompt[-2:] == ')#':
            return True
        else:
            return False
