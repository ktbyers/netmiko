from __future__ import unicode_literals
from netmiko.huawei.huawei_ssh import HuaweiSSH, HuaweiVrpv8SSH

# import customize class
from netmiko.huawei.huawei_ssh import HuaweiTelnet, HuaweiSerial

__all__ = ["HuaweiSSH", "HuaweiVrpv8SSH"
           # customize class
           "HuaweiTelnet",
           "HuaweiSerial",
]
