from netmiko.ssh_connection import SSHConnection
from netmiko.netmiko_globals import MAX_BUFFER

import re
import time

class HPProcurveSSH(SSHConnection):

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

        # HP sends up - 'Press any key to continue'
        time.sleep(1)
        self.remote_conn.send("\n")
        time.sleep(1)

        self.disable_paging()
        self.find_prompt()


    def disable_paging(self, delay_factor=1):
        '''
        Ensures that multi-page output doesn't prompt for user interaction 
        (i.e. --MORE--)

        Must manually control the channel at this point.
        '''

        self.remote_conn.send("\n")
        self.remote_conn.send("no page\n")
        time.sleep(1*delay_factor)

        output = self.remote_conn.recv(MAX_BUFFER)
        return output


    def strip_ansi_escape_codes(self, string_buffer):
        '''
        Remove any ANSI (VT100) ESC codes from the output

        Note: this does not capture ALL possible ANSI Escape Codes only the ones
        I have encountered
        
        Current codes that are filtered:
        ^[[24;27H   Position cursor
        ^[[?25h     Show the cursor
        ^[E         Next line
        ^[[2K       Erase line
        ^[[1;24r    Enable scrolling from start to row end
        0x1b = is the escape character [^ in hex

        '''

        DEBUG = False
        if DEBUG: print "In strip_ansi_escape_codes"
        if DEBUG: print "repr = %s" % repr(string_buffer)

        CODE_POSITION_CURSOR = '\x1b\[\d+;\d+H'
        CODE_SHOW_CURSOR = '\x1b\[\?25h'
        CODE_NEXT_LINE = '\x1bE'
        CODE_ERASE_LINE = '\x1b\[2K'
        CODE_ENABLE_SCROLL = '\x1b\[\d+;\d+r'

        CODE_SET = [ CODE_POSITION_CURSOR, CODE_SHOW_CURSOR, CODE_ERASE_LINE, CODE_ENABLE_SCROLL ] 

        output = string_buffer
        for ansi_esc_code in CODE_SET:
            output = re.sub(ansi_esc_code, '', output)

        # CODE_NEXT_LINE must substitute with '\n'
        output = re.sub(CODE_NEXT_LINE, '\n', output)

        if DEBUG:
            print "new_output = %s" % output
            print "repr = %s" % repr(output)
        
        return output


    def enable(self):
        '''
        Enter enable mode

        Not implemented on ProCurve just SSH as Manager
        '''

        return None
