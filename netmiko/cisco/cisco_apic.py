"""Subclass specific to Cisco APIC."""

from netmiko.linux.linux_ssh import LinuxSSH


class CiscoApicSSH(LinuxSSH):
    """
    Subclass specific to Cisco APIC.

    This class inherit from LinuxSSH because Cisco APIC is based on Linux
    """

    pass
