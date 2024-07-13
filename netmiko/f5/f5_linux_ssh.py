from netmiko.linux.linux_ssh import LinuxSSH
import re

class F5LinuxSSH(LinuxSSH):


    def find_failover(self) -> str:

        #command = 'show failover'
        pattern_act = 'Active'
        pattern_stby = 'Standby'
        pattern_off = 'Standalone'

        output = self.find_prompt()

        if re.search(pattern_off, output):
            return "Off"

        elif re.search(pattern_act, output):
            return "Active"

        elif re.search(pattern_stby, output):
            return "Standby"

        else:
            raise ValueError("Act/Stby Pattern Error")
            return None

