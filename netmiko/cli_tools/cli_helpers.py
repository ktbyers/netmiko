from typing import Any, Dict
from netmiko.utilities import load_devices, obtain_all_devices


def obtain_devices(device_or_group: str) -> Dict[str, Dict[str, Any]]:
    """
    Obtain the devices from the .netmiko.yml file using either a group-name or
    a device-name. A group-name will be a list of device-names. A device-name
    will just be a dictionary of device parameters (ConnectHandler **kwargs).
    """
    my_devices = load_devices()
    if device_or_group == "all":
        devices = obtain_all_devices(my_devices)
    else:
        try:
            singledevice_or_group = my_devices[device_or_group]
            devices = {}
            if isinstance(singledevice_or_group, list):
                # Group of Devices
                device_group = singledevice_or_group
                for device_name in device_group:
                    devices[device_name] = my_devices[device_name]
            else:
                # Single Device (dictionary)
                device_name = device_or_group
                device_dict = my_devices[device_name]
                devices[device_name] = device_dict
        except KeyError:
            return (
                "Error reading from netmiko devices file."
                " Device or group not found: {0}".format(device_or_group)
            )

    return devices
