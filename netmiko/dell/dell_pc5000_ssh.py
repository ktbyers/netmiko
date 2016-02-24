'''
Netmiko support for Dell PowerConnect 5XXX switch
'''
from __future__ import print_function
from __future__ import unicode_literals

import time
import socket
import os
from errno import ECONNREFUSED, EHOSTUNREACH
import paramiko

from paramiko.ssh_exception import (
    BadHostKeyException, NoValidConnectionsError
)

from netmiko.netmiko_globals import MAX_BUFFER
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
from netmiko.ssh_connection import SSHConnection


class DellPowerConnect5000SSH(SSHConnection):
    '''
    Netmiko support for Dell PowerConnect 5XXX switch
    '''

    def __init__(self, *args, **kwargs):
        self._system_host_keys = paramiko.hostkeys.HostKeys()
        self._host_keys = paramiko.hostkeys.HostKeys()
        self._policy = paramiko.client.RejectPolicy()
        self._host_keys_filename = None
        self._log_channel = None
        super(DellPowerConnect5000SSH, self).__init__(*args, **kwargs)

    def establish_connection(self, sleep_time=3, verbose=True, timeout=8,
                             use_keys=False, key_file=None):
        '''
        Establish SSH connection to the network device

        Timeout will generate a NetMikoTimeoutException
        Authentication failure will generate a NetMikoAuthenticationException

        use_keys is a boolean that allows ssh-keys to be used for authentication
        '''

        # Convert Paramiko connection parameters to a dictionary
        ssh_connect_params = self._connect_params_dict(use_keys=use_keys, key_file=key_file,
                                                       timeout=timeout)

        # Check if using SSH 'config' file mainly for SSH proxy support (updates ssh_connect_params)
        if self.ssh_config_file:
            self._use_ssh_config(ssh_connect_params)

        errors = {}
        sock = None
        to_try = list(self._families_and_addresses(ssh_connect_params['hostname'],
                                                   ssh_connect_params['port']))
        for af, addr in to_try:
            try:
                sock = socket.socket(af, socket.SOCK_STREAM)
                if timeout is not None:
                    try:
                        sock.settimeout(timeout)
                    except:
                        pass
                paramiko.util.retry_on_signal(lambda: sock.connect(addr))
                # Break out of the loop on success
                break
            except socket.error as e:
                    # Raise anything that isn't a straight up connection error
                    # (such as a resolution error)
                if e.errno not in (ECONNREFUSED, EHOSTUNREACH):
                    raise
                    # Capture anything else so we know how the run looks once
                    # iteration is complete. Retain info about which attempt
                    # this was.
                errors[addr] = e

            # Make sure we explode usefully if no address family attempts
            # succeeded. We've no way of knowing which error is the "right"
            # one, so we construct a hybrid exception containing all the real
            # ones, of a subclass that client code should still be watching for
            # (socket.error)
        if len(errors) == len(to_try):
            raise NoValidConnectionsError(errors)


        t = paramiko.Transport(sock)
        # FIXME: add crompression support
        # FIXME: add pubkey support
        t.start_client()

        # Load host_keys for better SSH security
        if self.system_host_keys:
            self.load_system_host_keys()
        if self.alt_host_keys and os.path.isfile(self.alt_key_file):
            self.load_host_keys(self.alt_key_file)

        server_key = t.get_remote_server_key()
        keytype = server_key.get_name()

        # Default is to automatically add untrusted hosts (make sure appropriate for your env)
        self._policy = self.key_policy

        if ssh_connect_params['port'] == paramiko.config.SSH_PORT:
            server_hostkey_name = ssh_connect_params['hostname']
        else:
            server_hostkey_name = "[%s]:%d" % (ssh_connect_params['hostname'],
                                               ssh_connect_params['port'])

        our_server_key = self._system_host_keys.get(server_hostkey_name,
                                                    {}).get(keytype, None)
        if our_server_key is None:
            our_server_key = self._host_keys.get(server_hostkey_name,
                                                 {}).get(keytype, None)
        if our_server_key is None:
            # will raise exception if the key is rejected; let that fall out
            self._policy.missing_host_key(self, server_hostkey_name,
                                          server_key)
            # if the callback returns, assume the key is ok
            our_server_key = server_key

        if server_key != our_server_key:
            raise BadHostKeyException(ssh_connect_params['hostname'],
                                      server_key, our_server_key)

        t.auth_none(ssh_connect_params['username'])
        self.remote_conn_pre = t.open_session()
        self.remote_conn_pre.get_pty()
        self.remote_conn_pre.invoke_shell()

        # initiate SSH connection
        try:
            while 1:
                if self.remote_conn_pre.recv_ready():
                    prompt = self.remote_conn_pre.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                    if 'name' in prompt.lower():
                        self.remote_conn_pre.send('{}\n'.format(ssh_connect_params['username']))
                    if 'password' in prompt.lower():
                        self.remote_conn_pre.send('{}\n'.format(ssh_connect_params['password']))
                        break

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

        # Use invoke_shell to establish an 'interactive session'
        self.remote_conn = self.remote_conn_pre
        self.special_login_handler()
        if verbose:
            print("Interactive SSH session established")

        time.sleep(sleep_time)
        # Strip any initial data
        if self.remote_conn.recv_ready():
            return self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
        else:
            i = 0
            while i <= 10:
                # Send a newline if no data is present
                self.remote_conn.sendall('\n')
                time.sleep(.5)
                if self.remote_conn.recv_ready():
                    return self.remote_conn.recv(MAX_BUFFER).decode('utf-8', 'ignore')
                else:
                    i += 1
            return ""

    def _log(self, *args, **kwargs):
        pass

    def session_preparation(self):
        self.disable_paging(command="terminal datadump\n")
        self.set_base_prompt()


    def load_system_host_keys(self, filename=None):
        """
        Load host keys from a system (read-only) file.  Host keys read with
        this method will not be saved back by `save_host_keys`.
        This method can be called multiple times.  Each new set of host keys
        will be merged with the existing set (new replacing old if there are
        conflicts).
        If ``filename`` is left as ``None``, an attempt will be made to read
        keys from the user's local "known hosts" file, as used by OpenSSH,
        and no exception will be raised if the file can't be read.  This is
        probably only useful on posix.
        :param str filename: the filename to read, or ``None``
        :raises IOError:
            if a filename was provided and the file could not be read
        """
        if filename is None:
            # try the user's .ssh key file, and mask exceptions
            filename = os.path.expanduser('~/.ssh/known_hosts')
            try:
                self._system_host_keys.load(filename)
            except IOError:
                pass
            return
        self._system_host_keys.load(filename)

    def load_host_keys(self, filename):
        """
        Load host keys from a local host-key file.  Host keys read with this
        method will be checked after keys loaded via `load_system_host_keys`,
        but will be saved back by `save_host_keys` (so they can be modified).
        The missing host key policy `.AutoAddPolicy` adds keys to this set and
        saves them, when connecting to a previously-unknown server.
        This method can be called multiple times.  Each new set of host keys
        will be merged with the existing set (new replacing old if there are
        conflicts).  When automatically saving, the last hostname is used.
        :param str filename: the filename to read
        :raises IOError: if the filename could not be read
        """
        self._host_keys_filename = filename
        self._host_keys.load(filename)


    def _families_and_addresses(self, hostname, port):
        """
        Yield pairs of address families and addresses to try for connecting.
        :param str hostname: the server to connect to
        :param int port: the server port to connect to
        :returns: Yields an iterable of ``(family, address)`` tuples
        """
        guess = True
        addrinfos = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for (family, socktype, proto, canonname, sockaddr) in addrinfos:
            if socktype == socket.SOCK_STREAM:
                yield family, sockaddr
                guess = False

        # some OS like AIX don't indicate SOCK_STREAM support, so just guess. :(
        # We only do this if we did not get a single result marked as socktype == SOCK_STREAM.
        if guess:
            for family, _, _, _, sockaddr in addrinfos:
                yield family, sockaddr
