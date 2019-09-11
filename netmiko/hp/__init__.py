from __future__ import unicode_literals
from netmiko.hp.hp_procurve import HPProcurveSSH, HPProcurveTelnet
from netmiko.hp.hp_comware import HPComwareSSH, HPComwareTelnet

# import customize class
from netmiko.hp.hp_comware import HPComwareSerial

__all__ = ["HPProcurveSSH", "HPProcurveTelnet", "HPComwareSSH", "HPComwareTelnet", 
            # customize class
            "HPComwareSerial"]
