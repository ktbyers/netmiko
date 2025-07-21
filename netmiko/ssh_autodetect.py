"""
The ssh_autodetect module is used to auto-detect the netmiko device_type to use to further initiate
a new SSH connection with a remote host. This auto-detection is based on a unique class called
**SSHDetect**.

Notes
-----

The **SSHDetect** class is instantiated using the same parameters than a standard Netmiko
connection (see the *netmiko.ssh_dispatacher.ConnectHandler* function). The only acceptable value
for the 'device_type' argument is 'autodetect'.

The auto-detection is solely based on *SSH_MAPPER_BASE*. The keys are the name of
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

from typing import Any, List, Optional, Union, Dict
import re
import time

import paramiko

from netmiko.ssh_dispatcher import ConnectHandler
from netmiko.base_connection import BaseConnection


# 'dispatch' key is the SSHDetect method to call. dispatch key will be popped off dictionary
# remaining keys indicate kwargs that will be passed to dispatch method.
# Note, the 'cmd' needs to avoid output paging.
SSH_MAPPER_DICT = {
    "alcatel_aos": {
        "cmd": "show system",
        "search_patterns": [r"Alcatel-Lucent"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "alcatel_sros": {
        "cmd": "show version",
        "search_patterns": ["Nokia", "Alcatel"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "allied_telesis_awplus": {
        "cmd": "show version",
        "search_patterns": ["AlliedWare Plus"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "apresia_aeos": {
        "cmd": "show system",
        "search_patterns": ["Apresia"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "arista_eos": {
        "cmd": "show version",
        "search_patterns": [r"Arista", r"vEOS"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "aruba_aoscx": {
        "cmd": "show version",
        "search_patterns": [r"ArubaOS-CX"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "ciena_saos": {
        "cmd": "software show",
        "search_patterns": [r"saos"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "ciena_waveserver": {
        "cmd": "software show",
        "search_patterns": [r"WAVESERVER"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_asa": {
        "cmd": "show version",
        "search_patterns": [r"Cisco Adaptive Security Appliance", r"Cisco ASA"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_ftd": {
        "cmd": "show version",
        "search_patterns": [r"Cisco Firepower"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_ios": {
        "cmd": "show version",
        "search_patterns": [
            "Cisco IOS Software",
            "Cisco Internetwork Operating System Software",
        ],
        "priority": 95,
        "dispatch": "_autodetect_std",
    },
    "cisco_xe": {
        "cmd": "show version",
        "search_patterns": [r"Cisco IOS XE Software"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_nxos": {
        "cmd": "show version",
        "search_patterns": [r"Cisco Nexus Operating System", r"NX-OS"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_xr": {
        "cmd": "show version",
        "search_patterns": [r"Cisco IOS XR"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_xr_2": {
        "cmd": "show version brief",
        "search_patterns": [r"Cisco IOS XR"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cumulus_linux": {
        "cmd": "uname -a",
        "search_patterns": [r"Linux cumulus"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "dell_force10": {
        "cmd": "show version",
        "search_patterns": [r"Real Time Operating System Software"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "dell_os9": {
        "cmd": "show system",
        "search_patterns": [
            r"Dell Application Software Version\s*:\s*9",
            r"Dell Networking OS Version\s*:\s*9",
            r"Dell EMC Networking OS Version\s*:\s*9",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "dell_os10": {
        "cmd": "show version",
        "search_patterns": [
            r"Dell EMC Networking OS10.Enterprise",
            r"Dell SmartFabric OS10[\s*|-]Enterprise",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "dell_powerconnect": {
        "cmd": "show system",
        "search_patterns": [r"PowerConnect"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "f5_tmsh": {
        "cmd": "show sys version",
        "search_patterns": [r"BIG-IP"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "f5_linux": {
        "cmd": "cat /etc/issue",
        "search_patterns": [r"BIG-IP"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "h3c_comware": {
        "cmd": "display version",
        "search_patterns": ["H3C Comware Software"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "hp_comware": {
        "cmd": "display version",
        "search_patterns": ["HPE Comware", "HP Comware"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "hp_procurve": {
        "cmd": "show version",
        "search_patterns": [r"Image stamp.*/code/build"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "huawei": {
        "cmd": "display version",
        "search_patterns": [
            r"Huawei Technologies",
            r"Huawei Versatile Routing Platform Software",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "juniper_junos": {
        "cmd": "show version",
        "search_patterns": [
            r"JUNOS Software Release",
            r"JUNOS .+ Software",
            r"JUNOS OS Kernel",
            r"JUNOS Base Version",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "linux": {
        "cmd": "uname -a",
        "search_patterns": [r"Linux"],
        "priority": 95,
        "dispatch": "_autodetect_std",
    },
    "ericsson_ipos": {
        "cmd": "show version",
        "search_patterns": [r"Ericsson IPOS Version"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "extreme_exos": {
        "cmd": "show version",
        "search_patterns": [r"ExtremeXOS", "EXOS"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "extreme_netiron": {
        "cmd": "show version",
        "search_patterns": [r"(NetIron|MLX)"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "extreme_slx": {
        "cmd": "show version",
        "search_patterns": [
            r"SLX-OS Operating System",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "extreme_tierra": {
        "cmd": "show version",
        "search_patterns": [r"TierraOS Software"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "ubiquiti_edgeswitch": {
        "cmd": "show version",
        "search_patterns": [r"EdgeSwitch"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_wlc": {
        "cmd": "",
        "dispatch": "_autodetect_remote_version",
        "search_patterns": [r"CISCO_WLC"],
        "priority": 99,
    },
    "cisco_wlc_85": {
        "cmd": "show inventory",
        "dispatch": "_autodetect_std",
        "search_patterns": [r"Cisco.*Wireless.*Controller"],
        "priority": 99,
    },
    "mellanox_mlnxos": {
        "cmd": "show version",
        "search_patterns": [r"Onyx", r"SX_PPC_M460EX"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "yamaha": {
        "cmd": "show copyright",
        "search_patterns": [r"Yamaha Corporation"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "fortinet": {
        "cmd": "get system status",
        "search_patterns": [r"FortiOS", r"FortiGate"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "paloalto_panos": {
        "cmd": "show system info",
        "search_patterns": [r"model:\s+PA"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "supermicro_smis": {
        "cmd": "show system info",
        "search_patterns": [r"Super Micro Computer"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "flexvnf": {
        "cmd": "show system package-info",
        "search_patterns": [r"Versa FlexVNF"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_viptela": {
        "cmd": "show system status",
        "search_patterns": [r"Viptela, Inc"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "oneaccess_oneos": {
        "cmd": "show version",
        "search_patterns": [r"OneOS"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "netgear_prosafe": {
        "cmd": "show version",
        "search_patterns": [r"ProSAFE"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "huawei_smartax": {
        "cmd": "display version",
        "search_patterns": [r"Huawei Integrated Access Software"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "nec_ix": {
        "cmd": "show hardware",
        "search_patterns": [r"IX Series"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "fiberstore_fsosv2": {
        "cmd": "show version",
        "search_patterns": [
            (
                r"Fiberstore Co., Limited Internetwork Operating System "
                r"Software[\s\S]*Version 2.[0-9]*.[0-9]*[\s\S]*"
            )
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "telcosystems_binos": {
        "cmd": "show version",
        "search_patterns": [r"BiNOS"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
}

# Sort SSH_MAPPER_DICT such that the most common commands are first
cmd_count: Dict[str, int] = {}
for k, v in SSH_MAPPER_DICT.items():
    my_cmd = v["cmd"]
    assert isinstance(my_cmd, str)
    count = cmd_count.setdefault(my_cmd, 0)
    cmd_count[my_cmd] = count + 1
cmd_count = {k: v for k, v in sorted(cmd_count.items(), key=lambda item: item[1])}

# SSH_MAPPER_BASE is a list
SSH_MAPPER_BASE = sorted(
    SSH_MAPPER_DICT.items(), key=lambda item: int(cmd_count[str(item[1]["cmd"])])
)
SSH_MAPPER_BASE.reverse()


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
    connection : netmiko.terminal_server.TerminalServerSSH
        A basic connection to the remote SSH end.
    potential_matches: dict
        Dict of (device_type, accuracy) that is populated through an interaction with the
        remote end.

    Methods
    -------
    autodetect()
        Try to determine the device type.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Constructor of the SSHDetect class
        """
        if kwargs["device_type"] != "autodetect":
            raise ValueError("The connection device_type must be 'autodetect'")
        # Always set cmd_verify to False for autodetect
        kwargs["global_cmd_verify"] = False
        self.connection = ConnectHandler(*args, **kwargs)

        # Add additional sleep to let the login complete.
        time.sleep(3)

        # Call the _test_channel_read() in base to clear initial data
        output = BaseConnection._test_channel_read(self.connection)
        self.initial_buffer = output
        self.potential_matches: Dict[str, int] = {}
        self._results_cache: Dict[str, str] = {}

    def autodetect(self) -> Union[str, None]:
        """
        Try to guess the best 'device_type' based on patterns defined in SSH_MAPPER_BASE

        Returns
        -------
        best_match : str or None
            The device type that is currently the best to use to interact with the device
        """
        for device_type, autodetect_dict in SSH_MAPPER_BASE:
            tmp_dict = autodetect_dict.copy()
            call_method = tmp_dict.pop("dispatch")
            assert isinstance(call_method, str)
            autodetect_method = getattr(self, call_method)
            accuracy = autodetect_method(**tmp_dict)
            if accuracy:
                self.potential_matches[device_type] = accuracy
                if accuracy >= 99:  # Stop the loop as we are sure of our match
                    best_match = sorted(
                        self.potential_matches.items(), key=lambda t: t[1], reverse=True
                    )
                    # WLC needs two different auto-dectect solutions
                    if "cisco_wlc_85" in best_match[0]:
                        best_match[0] = ("cisco_wlc", 99)
                    # IOS XR needs two different auto-dectect solutions
                    if "cisco_xr_2" in best_match[0]:
                        best_match[0] = ("cisco_xr", 99)
                    self.connection.disconnect()
                    return best_match[0][0]

        if not self.potential_matches:
            self.connection.disconnect()
            return None

        best_match = sorted(
            self.potential_matches.items(), key=lambda t: t[1], reverse=True
        )
        self.connection.disconnect()
        return best_match[0][0]

    def _send_command(self, cmd: str = "") -> str:
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
        output = self.connection.read_channel_timing(last_read=6.0)
        output = self.connection.strip_backspaces(output)
        return output

    def _send_command_wrapper(self, cmd: str) -> str:
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

    def _autodetect_remote_version(
        self,
        search_patterns: Optional[List[str]] = None,
        re_flags: int = re.IGNORECASE,
        priority: int = 99,
        **kwargs: Any
    ) -> int:
        """
        Method to try auto-detect the device type, by matching a regular expression on the reported
        remote version of the SSH server.

        Parameters
        ----------
        search_patterns : list
            A list of regular expression to look for in the reported remote SSH version
            (default: None).
        re_flags: re.flags, optional
            Any flags from the python re module to modify the regular expression (default: re.I).
        priority: int, optional
            The confidence the match is right between 0 and 99 (default: 99).
        """
        invalid_responses = [r"^$"]

        if not search_patterns:
            return 0

        try:
            remote_conn = self.connection.remote_conn
            assert isinstance(remote_conn, paramiko.Channel)
            assert remote_conn.transport is not None
            remote_version = remote_conn.transport.remote_version
            for pattern in invalid_responses:
                match = re.search(pattern, remote_version, flags=re.I)
                if match:
                    return 0
            for pattern in search_patterns:
                match = re.search(pattern, remote_version, flags=re_flags)
                if match:
                    return priority
        except Exception:
            return 0
        return 0

    def _autodetect_std(
        self,
        cmd: str = "",
        search_patterns: Optional[List[str]] = None,
        re_flags: int = re.IGNORECASE,
        priority: int = 99,
    ) -> int:
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
            r"% Invalid input detected",
            r"syntax error, expecting",
            r"Error: Unrecognized command",
            r"%Error",
            r"command not found",
            r"Syntax Error: unexpected argument",
            r"% Unrecognized command found at",
            r"% Unknown command, the error locates at",
        ]
        if not cmd or not search_patterns:
            return 0
        try:
            # _send_command_wrapper will use already cached results if available
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
