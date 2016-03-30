from netmiko.ssh_connection import SSHConnection
import paramiko
import time
import socket

from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException


class FortinetSSH(SSHConnection):

    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self.set_base_prompt(pri_prompt_terminator='$')
        self.disable_paging()

    def disable_paging(self, delay_factor=.1):
        """Disable paging is only available with specific roles so it may fail."""
        check_command = "get system status\n"
        output = self.send_command(check_command)
        self.allow_disable_global = True
        self.vdoms = False

        # According with http://www.gossamer-threads.com/lists/rancid/users/6729
        if output.find("Virtual domain configuration: enable"):
            self.vdoms = True
            vdom_additional_command = "config global"
            output = self.send_command(vdom_additional_command)
            if output.find("Command fail"):
                self.allow_disable_global = False
                self.remote_conn.close()
                self.establish_connection(width=100, height=1000)

        new_output = ''
        if self.allow_disable_global:
            disable_paging_commands = ["config system console", "set output standard", "end"]
            outputlist = [self.send_command(command) for command in disable_paging_commands]
            # Should test output is valid
            new_output = "\n".join(outputlist)

        return output + new_output

    def cleanup(self):
        '''Re-enable paging globally'''
        if self.allow_disable_global:
            enable_paging_commands = ["config system console", "set output more", "end"]
            if self.vdoms:
                enable_paging_commands.insert(0, "config global")
            # Should test output is valid
            for command in enable_paging_commands:
                self.send_command(command)

    def establish_connection(self, sleep_time=3, verbose=True, timeout=8, use_keys=False,
                             key_file=None, width=None, height=None):
        """Special Fortinet handler for SSH connection"""
        self.remote_conn_pre = paramiko.SSHClient()
        self.remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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

        # Since Fortinet paging setting is global use terminal settings instead (if necessary)
        if width and height:
            self.remote_conn = self.remote_conn_pre.invoke_shell(term='vt100',
                                                                 width=width,
                                                                 height=height)
        else:
            self.remote_conn = self.remote_conn_pre.invoke_shell()
        self.remote_conn.settimeout(timeout)
        if verbose:
            print("Interactive SSH session established")

        i = 0
        while i <= 100:
            time.sleep(.1)
            if self.remote_conn.recv_ready():
                return self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
            else:
                # Send a newline if no data is present
                self.remote_conn.sendall('\n')
                i += 1

        return ""

    def config_mode(self, config_command=''):
        '''No config mode for Fortinet devices'''
        return ''

    def exit_config_mode(self, exit_config=''):
        '''No config mode for Fortinet devices'''
        return ''
