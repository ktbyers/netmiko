"""
The ssh_autodetect module is used to auto-detect the netmiko device_type to use to further initiate
a new SSH connection with a remote host. This auto-detection is based on a unique class called
**SSHDetect**.

Notes
-----

The **SSHDetect** class is instantiated using the same parameters than a standard Netmiko
connection (see the *netmiko.ssh_dispatacher.ConnectHandler* function). The only acceptable value
for the 'device_type' argument is 'autodetect'.

The auto-detection is solely based on the *SSH_MAPPER_BASE* dictionary. The keys are the name of
the 'device_type' supported for auto-detection and the value is another dictionary describing how
to handle the auto-detection.

* "cmd" : The command to send to the remote device. **The command output must not require paging.**
* "search_patterns" : A list of regex to compare with the output of the command
* "priority" : An integer (0-99) which specifies the confidence of the match above
* "dispatch" : The function to call to try the autodetection (per default SSHDetect._autodetect_std)

Examples
--------

# Auto-detection section
>>> from netmiko.ssh_autodetect import SSHDetect
>>> from netmiko.ssh_dispatcher import ConnectHandler
>>> remote_device = {'device_type': 'autodetect',
                     'host': 'remote.host',
                     'username': 'test',
                     'password': 'foo'}
>>> guesser = SSHDetect(**remote_device)
>>> best_match = guesser.autodetect()
>>> print(best_match) # Name of the best device_type to use further
>>> print(guesser.potential_matches) # Dictionary of the whole matching result

# Netmiko connection creation section
>>> remote_device['device_type'] = best_match
>>> connection = ConnectHandler(**remote_device)
"""
from __future__ import unicode_literals

import re
import time
from netmiko.ssh_dispatcher import ConnectHandler
from netmiko.base_connection import BaseConnection


# 'dispatch' key is the SSHDetect method to call. dispatch key will be popped off dictionary
# remaining keys indicate kwargs that will be passed to dispatch method.
# Note, the 'cmd' needs to avoid output paging.
SSH_MAPPER_BASE = {
    'alcatel_aos': {
        "cmd": "show system",
        "search_patterns": ["Alcatel-Lucent"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'alcatel_sros': {
        "cmd": "show version | match TiMOS",
        "search_patterns": [
            "Nokia",
            "Alcatel",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'arista_eos': {
        "cmd": "show version | inc rist",
        "search_patterns": ["Arista"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'cisco_ios': {
        "cmd": "show version | inc Cisco",
        "search_patterns": [
           "Cisco IOS Software",
           "Cisco Internetwork Operating System Software"
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'cisco_asa': {
        "cmd": "show version | inc Cisco",
        "search_patterns": ["Cisco Adaptive Security Appliance", "Cisco ASA"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'cisco_nxos': {
        "cmd": "show version | inc Cisco",
        "search_patterns": ["Cisco Nexus Operating System", "NX-OS"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'cisco_xr': {
        "cmd": "show version | inc Cisco",
        "search_patterns": ["Cisco IOS XR"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'huawei': {
        "cmd": "display version | inc Huawei",
        "search_patterns": [
            "Huawei Technologies",
            "Huawei Versatile Routing Platform Software"
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'juniper_junos': {
        "cmd": "show version | match JUNOS",
        "search_patterns": [
            "JUNOS Software Release",
            "JUNOS .+ Software",
            "JUNOS OS Kernel",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    'dell_force10': {
        "cmd": "show version | grep Type",
        "search_patterns": ["S4048-ON"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
}


class SSHDetect(object):
    """
    The SSHDetect class tries to automatically guess the device type running on the SSH remote end.
    Be careful that the kwargs 'device_type' must be set to 'autodetect', otherwise it won't work at
    all.

    Parameters
    ----------
    *args : list
        The same *args that you might provide to the netmiko.ssh_dispatcher.ConnectHandler.
    *kwargs : dict
        The same *kwargs that you might provide to the netmiko.ssh_dispatcher.ConnectHandler.

    Attributes
    ----------
    connection : netmiko.terminal_server.TerminalServer
        A basic connection to the remote SSH end.
    potential_matches: dict
        Dict of (device_type, accuracy) that is populated through an interaction with the
        remote end.

    Methods
    -------
    autodetect()
        Try to determine the device type.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor of the SSHDetect class
        """
        if kwargs["device_type"] != "autodetect":
            raise ValueError("The connection device_type must be 'autodetect'")
        self.connection = ConnectHandler(*args, **kwargs)
        # Call the _test_channel_read() in base to clear initial data
        output = BaseConnection._test_channel_read(self.connection)
        self.initial_buffer = output
        self.potential_matches = {}
        self._results_cache = {}

    def autodetect(self):
        """
        Try to guess the best 'device_type' based on patterns defined in SSH_MAPPER_BASE

        Returns
        -------
        best_match : str or None
            The device type that is currently the best to use to interact with the device
        """
        for device_type, autodetect_dict in SSH_MAPPER_BASE.items():
            tmp_dict = autodetect_dict.copy()
            call_method = tmp_dict.pop("dispatch")
            autodetect_method = getattr(self, call_method)
            accuracy = autodetect_method(**tmp_dict)
            if accuracy:
                self.potential_matches[device_type] = accuracy
                if accuracy >= 99:  # Stop the loop as we are sure of our match
                    best_match = sorted(self.potential_matches.items(), key=lambda t: t[1],
                                        reverse=True)
                    self.connection.disconnect()
                    return best_match[0][0]

        if not self.potential_matches:
            self.connection.disconnect()
            return None

        best_match = sorted(self.potential_matches.items(), key=lambda t: t[1], reverse=True)
        self.connection.disconnect()
        return best_match[0][0]

    def _send_command(self, cmd=""):
        """
        Handle reading/writing channel directly. It is also sanitizing the output received.

        Parameters
        ----------
        cmd : str, optional
            The command to send to the remote device (default : "", just send a new line)

        Returns
        -------
        output : str
            The output from the command sent
        """
        self.connection.write_channel(cmd + "\n")
        time.sleep(1)
        output = self.connection._read_channel_timing()
        output = self.connection.strip_ansi_escape_codes(output)
        output = self.connection.strip_backspaces(output)
        return output

    def _send_command_wrapper(self, cmd):
        """
        Send command to the remote device with a caching feature to avoid sending the same command
        twice based on the SSH_MAPPER_BASE dict cmd key.

        Parameters
        ----------
        cmd : str
            The command to send to the remote device after checking cache.

        Returns
        -------
        response : str
            The response from the remote device.
        """
        cached_results = self._results_cache.get(cmd)
        if not cached_results:
            response = self._send_command(cmd)
            self._results_cache[cmd] = response
            return response
        else:
            return cached_results

    def _autodetect_std(self, cmd="", search_patterns=None, re_flags=re.I, priority=99):
        """
        Standard method to try to auto-detect the device type. This method will be called for each
        device_type present in SSH_MAPPER_BASE dict ('dispatch' key). It will attempt to send a
        command and match some regular expression from the ouput for each entry in SSH_MAPPER_BASE
        ('cmd' and 'search_pattern' keys).

        Parameters
        ----------
        cmd : str
            The command to send to the remote device after checking cache.
        search_patterns : list
            A list of regular expression to look for in the command's output (default: None).
        re_flags: re.flags, optional
            Any flags from the python re module to modify the regular expression (default: re.I).
        priority: int, optional
            The confidence the match is right between 0 and 99 (default: 99).
        """
        invalid_responses = [
            r'% Invalid input detected',
            r'syntax error, expecting',
            r'Error: Unrecognized command',
            r'%Error'
        ]
        if not cmd or not search_patterns:
            return 0
        try:
            response = self._send_command_wrapper(cmd)
            # Look for error conditions in output
            for pattern in invalid_responses:
                match = re.search(pattern, response, flags=re.I)
                if match:
                    return 0
            for pattern in search_patterns:
                match = re.search(pattern, response, flags=re_flags)
                if match:
                    return priority
        except Exception:
            return 0
        return 0
