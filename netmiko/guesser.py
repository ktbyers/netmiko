"""
The guesser module is used to Guess the type of a device in order to automatically create a Netmiko ConnectionClass.
This will avoid to hard code the 'device_type' attribute when using the ConnectHandler function from Netmiko.

This constant dict is matching a 'device type' with 3 defined objects:
* The OID to GET
* The regular Expression to match for the OID value you retrieve
* The priority of the type (the highest the priority is, the better match it will be)
"""

import re
try:
    from pysnmp.entity.rfc3413.oneliner import cmdgen
except ImportError:
    raise ImportError("pysnmp not installed; please install it: 'pip install pysnmp'")

from netmiko.ssh_dispatcher import CLASS_MAPPER

SNMP_MAPPER_BASE = {
    'cisco_ios': {"oid": ".1.3.6.1.2.1.1.1.0",
                  "expr": re.compile(".*Cisco IOS Software,.*", re.IGNORECASE),
                  "priority": 60},
    'cisco_xe': {"oid": ".1.3.6.1.2.1.1.1.0",
                 "expr": re.compile(".*IOS-XE Software,.*", re.IGNORECASE),
                 "priority": 99},
    'cisco_asa': {"oid": ".1.3.6.1.2.1.1.1.0",
                  "expr": re.compile(".*Cisco Adaptive Security Appliance.*", re.IGNORECASE),
                  "priority": 99},
    'cisco_nxos': {"oid": ".1.3.6.1.2.1.1.1.0",
                   "expr": re.compile(".*Cisco NX-OS.*", re.IGNORECASE),
                   "priority": 99},
    'cisco_wlc': {"oid": ".1.3.6.1.2.1.1.1.0",
                  "expr": re.compile(".*Cisco Controller.*", re.IGNORECASE),
                  "priority": 99},
    'f5_ltm': {"oid": ".1.3.6.1.4.1.3375.2.1.4.1.0",
               "expr": re.compile(".*BIG-IP.*", re.IGNORECASE),
               "priority": 99},
    'fortinet': {"oid": ".1.3.6.1.2.1.1.1.0",
                 "expr": re.compile("Forti.*", re.IGNORECASE),
                 "priority": 80},
    'dummy': {"oid": ".1.3.6.1.2.1.1.1.0",
              "expr": re.compile("", re.IGNORECASE),
              "priority": 0}
}

# Build SNMP_MAPPER including _ssh and _telnet; initialize unsupported types to None
std_device_types = list(CLASS_MAPPER.keys())
SNMP_MAPPER = {}
for device_type in std_device_types:
    if '_ssh' in device_type or '_telnet' in device_type:
        continue
    if SNMP_MAPPER_BASE.get(device_type):
        SNMP_MAPPER[device_type] = SNMP_MAPPER_BASE[device_type]
    else:
        SNMP_MAPPER[device_type] = None

    alt_format1 = device_type + "_ssh"
    alt_format2 = device_type + "_telnet"
    for alt_format in (alt_format1, alt_format2):
        if CLASS_MAPPER.get(alt_format):
            SNMP_MAPPER[alt_format] = SNMP_MAPPER[device_type]

print(SNMP_MAPPER)


def available_type():
    """
    Find out which device type are supported for guessing.

    Returns
    -------
    list
        A list of device type that supports auto guessing.
    """
    return [name for name, value in SNMP_MAPPER.iteritems() if value]


class Guesser(object):
    """
    The Guesser class tries to 'guess' the type of the device you are trying to SSH into using SNMP. Most of the time
    the guesser is trying to find the device's type based on SNMP *SysDescr* and regular expression.

    Parameters
    ----------
    device : str
        The name or IP address of the device we want to guess the type
    snmp_version : str, optional ('v1', 'v2c' or 'v3')
        The SNMP version that is running on the device (default: 'v2c')
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
    auth_proto : str, optional ('des', '3des', 'aes128', 'aes192', 'aes256', 'none')
        The SNMPv3 authentication protocol (default: 'aes256')
    encrypt_proto : str, optional ('sha', 'md5', 'none')
        The SNMPv3 encryption protocol (default: 'sha')

    Attributes
    ----------
    device : str
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
    guess()
        Try to guess the device type.

    """
    def __init__(self, device, snmp_version="v2c", snmp_port=161, community=None, user="", auth_key="", encrypt_key="",
                 auth_proto="sha", encrypt_proto="aes256"):
        """
        Constructor of Guesser class
        """
        # Check that the SNMP version is matching predefined type or raise ValueError
        if snmp_version == "v1" or snmp_version == "v2c":
            if not community:
                raise ValueError("When setting SNMP version 'v1' or 'v2c', the 'community' arguments must be set")
        elif snmp_version == "v3":
            if not user:
                raise ValueError("When setting SNMP version 'v3', the 'user' and 'password' arguments must be set")
        else:
            raise ValueError("SNMP version must be set to 'v1', 'v2c' or 'v3'")

        # Check that the SNMPv3 auth & priv parameters are matching predefined type or raise ValueError
        self._snmp_v3_authentication = {"sha": cmdgen.usmHMACSHAAuthProtocol, "md5": cmdgen.usmHMACMD5AuthProtocol,
                                        "none": cmdgen.usmNoAuthProtocol}
        self._snmp_v3_encryption = {"des": cmdgen.usmDESPrivProtocol, "3des": cmdgen.usm3DESEDEPrivProtocol,
                                    "aes128": cmdgen.usmAesCfb128Protocol, "aes192": cmdgen.usmAesCfb192Protocol,
                                    "aes256": cmdgen.usmAesCfb256Protocol, "none": cmdgen.usmNoPrivProtocol}
        if auth_proto not in self._snmp_v3_authentication.keys():
            raise ValueError("SNMP V3 'auth_proto' argument must have the following values: {}"
                             .format(self._snmp_v3_authentication.keys()))
        if encrypt_proto not in self._snmp_v3_encryption.keys():
            raise ValueError("SNMP V3 'encrypt_proto' argument must have the following values: {}"
                             .format(self._snmp_v3_encryption.keys()))

        self.device = device
        self.snmp_version = snmp_version
        self.snmp_port = snmp_port
        self.community = community
        self.user = user
        self.auth_key = auth_key
        self.encrypt_key = encrypt_key
        self.auth_proto = self._snmp_v3_authentication[auth_proto]
        self.encryp_proto = self._snmp_v3_encryption[encrypt_proto]

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
        snmp_target = (self.device, self.snmp_port)
        cmd_gen = cmdgen.CommandGenerator()

        (error_detected, error_status, error_index, snmp_data) = cmd_gen.getCmd(
            cmdgen.UsmUserData(self.user, self.auth_key, self.encrypt_key,
                               authProtocol=self.auth_proto,
                               privProtocol=self.encryp_proto),
            cmdgen.UdpTransportTarget(snmp_target, timeout=1.5, retries=2),
            oid,
            lookupNames=True,
            lookupValues=True)

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
        snmp_target = (self.device, self.snmp_port)
        cmd_gen = cmdgen.CommandGenerator()

        (error_detected, error_status, error_index, snmp_data) = cmd_gen.getCmd(
            cmdgen.CommunityData(self.community),
            cmdgen.UdpTransportTarget(snmp_target, timeout=1.5, retries=2),
            oid,
            lookupNames=True,
            lookupValues=True)

        if not error_detected and snmp_data[0][1]:
            return str(snmp_data[0][1])

        return ""

    def guess(self):
        """
        Try to guess the device type using SNMP GET based on the SNMP_MAPPER dict. The type which is returned is
        directly matching the name in *netmiko.ssh_dispatcher.CLASS_MAPPER_BASE* dict.

        Thus you can use this name to retrieve automatically the right ConnectionClass

        Returns
        -------
        potential_type : str
            The name of the device type that must be running.
        """
        oids = {}  # Hold all OIDs that needs to be retrieved (many are duplicate of SysDescr)
        for value in SNMP_MAPPER.values():
            if value:
                oids[value["oid"]] = None

        for oid in oids:
            if self.snmp_version in ["v1", "v2c"]:
                oids[oid] = self._get_snmpv2c(oid)
            else:
                oids[oid] = self._get_snmpv3(oid)

        potential_type = "dummy"
        mapper = {k: v for k, v in SNMP_MAPPER.items() if v}  # /!\ Only keep device_type that are defined
        for name, value in mapper.items():
            if value["expr"].match(oids[value["oid"]]) and value["priority"] > mapper[potential_type]["priority"]:
                potential_type = name  # Update the potential type only if matching expr and priority is higher
                if value["priority"] == 99:
                    break  # Stop iterating over all device type if the priority is 99
        return potential_type

if __name__ == "__main__":
    """
    Testing purposes only
    """
