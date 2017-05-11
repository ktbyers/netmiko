"""
This module is used to auto-detect the type of a device in order to automatically create a
Netmiko connection.

The will avoid to hard coding the 'device_type' when using the ConnectHandler factory function
from Netmiko.

Example:
------------------
from netmiko.snmp_autodetect import SNMPDetect

my_snmp = SNMPDetect(hostname='1.1.1.70', user='pysnmp', auth_key='key1', encrypt_key='key2')
device_type = my_snmp.autodetect()
------------------

autodetect will return None if no match.

SNMPDetect class defaults to SNMPv3

Note, pysnmp is a required dependency for SNMPDetect and is intentionally not included in
netmiko requirements. So installation of pysnmp might be required.
"""
from __future__ import unicode_literals

import re
try:
    from pysnmp.entity.rfc3413.oneliner import cmdgen
except ImportError:
    raise ImportError("pysnmp not installed; please install it: 'pip install pysnmp'")

from netmiko.ssh_dispatcher import CLASS_MAPPER


# Higher priority indicates a better match.
SNMP_MAPPER_BASE = {
    'arista_eos': {"oid": ".1.3.6.1.2.1.1.1.0",
                   "expr": re.compile(r".*Arista Networks EOS.*", re.IGNORECASE),
                   "priority": 99},
    'hp_comware': {"oid": ".1.3.6.1.2.1.1.1.0",
                   "expr": re.compile(r".*HP Comware.*", re.IGNORECASE),
                   "priority": 99},
    'cisco_ios': {"oid": ".1.3.6.1.2.1.1.1.0",
                  "expr": re.compile(r".*Cisco IOS Software,.*", re.IGNORECASE),
                  "priority": 60},
    'cisco_xe': {"oid": ".1.3.6.1.2.1.1.1.0",
                 "expr": re.compile(r".*IOS-XE Software,.*", re.IGNORECASE),
                 "priority": 99},
    'cisco_xr': {"oid": ".1.3.6.1.2.1.1.1.0",
                 "expr": re.compile(r".*Cisco IOS XR Software.*", re.IGNORECASE),
                 "priority": 99},
    'cisco_asa': {"oid": ".1.3.6.1.2.1.1.1.0",
                  "expr": re.compile(r".*Cisco Adaptive Security Appliance.*", re.IGNORECASE),
                  "priority": 99},
    'cisco_nxos': {"oid": ".1.3.6.1.2.1.1.1.0",
                   "expr": re.compile(r".*Cisco NX-OS.*", re.IGNORECASE),
                   "priority": 99},
    'cisco_wlc': {"oid": ".1.3.6.1.2.1.1.1.0",
                  "expr": re.compile(r".*Cisco Controller.*", re.IGNORECASE),
                  "priority": 99},
    'f5_ltm': {"oid": ".1.3.6.1.4.1.3375.2.1.4.1.0",
               "expr": re.compile(r".*BIG-IP.*", re.IGNORECASE),
               "priority": 99},
    'fortinet': {"oid": ".1.3.6.1.2.1.1.1.0",
                 "expr": re.compile(r"Forti.*", re.IGNORECASE),
                 "priority": 80},
    'checkpoint': {"oid": ".1.3.6.1.4.1.2620.1.6.16.9.0",
                   "expr": re.compile(r"CheckPoint"),
                   "priority": 79},
}

# Ensure all SNMP device types are supported by Netmiko
SNMP_MAPPER = {}
std_device_types = list(CLASS_MAPPER.keys())
for device_type in std_device_types:
    if SNMP_MAPPER_BASE.get(device_type):
        SNMP_MAPPER[device_type] = SNMP_MAPPER_BASE[device_type]


class SNMPDetect(object):
    """
    The SNMPDetect class tries to automatically determine the device type.

    Typically this will use the MIB-2 SysDescr and regular expressions.

    Parameters
    ----------
    hostname: str
        The name or IP address of the hostname we want to guess the type
    snmp_version : str, optional ('v1', 'v2c' or 'v3')
        The SNMP version that is running on the device (default: 'v3')
    snmp_port : int, optional
        The UDP port on which SNMP is listening (default: 161)
    community : str, optional
        The SNMP read community when using SNMPv2 (default: None)
    user : str, optional
        The SNMPv3 user for authentication (default: '')
    auth_key : str, optional
        The SNMPv3 authentication key (default: '')
    encrypt_key : str, optional
        The SNMPv3 encryption key (default: '')
    auth_proto : str, optional ('des', '3des', 'aes128', 'aes192', 'aes256')
        The SNMPv3 authentication protocol (default: 'aes128')
    encrypt_proto : str, optional ('sha', 'md5')
        The SNMPv3 encryption protocol (default: 'sha')

    Attributes
    ----------
    hostname: str
        The name or IP address of the device we want to guess the type
    snmp_version : str
        The SNMP version that is running on the device
    snmp_port : int
        The UDP port on which SNMP is listening
    community : str
        The SNMP read community when using SNMPv2
    user : str
        The SNMPv3 user for authentication
    auth_key : str
        The SNMPv3 authentication key
    encrypt_key : str
        The SNMPv3 encryption key
    auth_proto : str
        The SNMPv3 authentication protocol
    encrypt_proto : str
        The SNMPv3 encryption protocol


    Methods
    -------
    autodetect()
        Try to determine the device type.

    """
    def __init__(self, hostname, snmp_version="v3", snmp_port=161, community=None, user="",
                 auth_key="", encrypt_key="", auth_proto="sha", encrypt_proto="aes128"):

        # Check that the SNMP version is matching predefined type or raise ValueError
        if snmp_version == "v1" or snmp_version == "v2c":
            if not community:
                raise ValueError("SNMP version v1/v2c community must be set.")
        elif snmp_version == "v3":
            if not user:
                raise ValueError("SNMP version v3 user and password must be set")
        else:
            raise ValueError("SNMP version must be set to 'v1', 'v2c' or 'v3'")

        # Check that the SNMPv3 auth & priv parameters match allowed types
        self._snmp_v3_authentication = {"sha": cmdgen.usmHMACSHAAuthProtocol,
                                        "md5": cmdgen.usmHMACMD5AuthProtocol}
        self._snmp_v3_encryption = {"des": cmdgen.usmDESPrivProtocol,
                                    "3des": cmdgen.usm3DESEDEPrivProtocol,
                                    "aes128": cmdgen.usmAesCfb128Protocol,
                                    "aes192": cmdgen.usmAesCfb192Protocol,
                                    "aes256": cmdgen.usmAesCfb256Protocol}
        if auth_proto not in self._snmp_v3_authentication.keys():
            raise ValueError("SNMP V3 'auth_proto' argument must be one of the following: {}"
                             .format(self._snmp_v3_authentication.keys()))
        if encrypt_proto not in self._snmp_v3_encryption.keys():
            raise ValueError("SNMP V3 'encrypt_proto' argument must be one of the following: {}"
                             .format(self._snmp_v3_encryption.keys()))

        self.hostname = hostname
        self.snmp_version = snmp_version
        self.snmp_port = snmp_port
        self.community = community
        self.user = user
        self.auth_key = auth_key
        self.encrypt_key = encrypt_key
        self.auth_proto = self._snmp_v3_authentication[auth_proto]
        self.encryp_proto = self._snmp_v3_encryption[encrypt_proto]
        self._response_cache = {}

    def _get_snmpv3(self, oid):
        """
        Try to send an SNMP GET operation using SNMPv3 for the specified OID.

        Parameters
        ----------
        oid : str
            The SNMP OID that you want to get.

        Returns
        -------
        string : str
            The string as part of the value from the OID you are trying to retrieve.
        """
        snmp_target = (self.hostname, self.snmp_port)
        cmd_gen = cmdgen.CommandGenerator()

        (error_detected, error_status, error_index, snmp_data) = cmd_gen.getCmd(
            cmdgen.UsmUserData(self.user, self.auth_key, self.encrypt_key,
                               authProtocol=self.auth_proto,
                               privProtocol=self.encryp_proto),
            cmdgen.UdpTransportTarget(snmp_target, timeout=1.5, retries=2),
            oid, lookupNames=True, lookupValues=True)

        if not error_detected and snmp_data[0][1]:
            return str(snmp_data[0][1])
        return ""

    def _get_snmpv2c(self, oid):
        """
        Try to send an SNMP GET operation using SNMPv2 for the specified OID.

        Parameters
        ----------
        oid : str
            The SNMP OID that you want to get.

        Returns
        -------
        string : str
            The string as part of the value from the OID you are trying to retrieve.
        """
        snmp_target = (self.hostname, self.snmp_port)
        cmd_gen = cmdgen.CommandGenerator()

        (error_detected, error_status, error_index, snmp_data) = cmd_gen.getCmd(
            cmdgen.CommunityData(self.community),
            cmdgen.UdpTransportTarget(snmp_target, timeout=1.5, retries=2),
            oid, lookupNames=True, lookupValues=True)

        if not error_detected and snmp_data[0][1]:
            return str(snmp_data[0][1])
        return ""

    def _get_snmp(self, oid):
        """Wrapper for generic SNMP call."""
        if self.snmp_version in ["v1", "v2c"]:
            return self._get_snmpv2c(oid)
        else:
            return self._get_snmpv3(oid)

    def autodetect(self):
        """
        Try to guess the device_type using SNMP GET based on the SNMP_MAPPER dict. The type which
        is returned is directly matching the name in *netmiko.ssh_dispatcher.CLASS_MAPPER_BASE*
        dict.

        Thus you can use this name to retrieve automatically the right ConnectionClass

        Returns
        -------
        potential_type : str
            The name of the device_type that must be running.
        """
        # Convert SNMP_MAPPER to a list and sort by priority
        snmp_mapper_list = []
        for k, v in SNMP_MAPPER.items():
            snmp_mapper_list.append({k: v})
        snmp_mapper_list = sorted(snmp_mapper_list, key=lambda x: list(x.values())[0]['priority'])
        snmp_mapper_list.reverse()

        for entry in snmp_mapper_list:
            for device_type, v in entry.items():
                oid = v['oid']
                regex = v['expr']

            # Used cache data if we already queryied this OID
            if self._response_cache.get(oid):
                snmp_response = self._response_cache.get(oid)
            else:
                snmp_response = self._get_snmp(oid)
                self._response_cache[oid] = snmp_response

            # See if we had a match
            if re.search(regex, snmp_response):
                return device_type

        return None
