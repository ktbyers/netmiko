from netmiko.huawei.huawei import HuaweiSSH, HuaweiVrpv8SSH
from netmiko.huawei.huawei import HuaweiTelnet
from netmiko.huawei.huawei_smartax import HuaweiSmartAXSSH
from netmiko.huawei.huawei_ont import HuaweiONTTelnet, HuaweiONTSSH

__all__ = [
    "HuaweiSmartAXSSH",
    "HuaweiSSH",
    "HuaweiVrpv8SSH",
    "HuaweiTelnet",
    "HuaweiONTTelnet",
    "HuaweiONTSSH",
]
