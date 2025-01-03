from typing import Any, Dict

from netmiko import ConnectHandler
from netmiko.utilities import obtain_all_devices, load_netmiko_yml
from netmiko.encryption_handling import decrypt_config, get_encryption_key
from netmiko.cli_tools import ERROR_PATTERN


def ssh_conn(device_name, device_params, cli_command=None, cfg_command=None):
    try:
        output = ""
        with ConnectHandler(**device_params) as net_connect:
            net_connect.enable()
            if cli_command:
                output += net_connect.send_command(cli_command)
            if cfg_command:
                output += net_connect.send_config_set(cfg_command)
            return device_name, output
    except Exception:
        return device_name, ERROR_PATTERN


def obtain_devices(device_or_group: str) -> Dict[str, Dict[str, Any]]:
    """
    Obtain the devices from the .netmiko.yml file using either a group-name or
    a device-name. A group-name will be a list of device-names. A device-name
    will just be a dictionary of device parameters (ConnectHandler **kwargs).
    """
    config_params, my_devices = load_netmiko_yml()
    use_encryption = config_params.get("encryption", False)
    encryption_type = config_params.get("encryption_type", "fernet")
    if use_encryption:
        key = get_encryption_key()
        my_devices = decrypt_config(my_devices, key, encryption_type)
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


def update_device_params(params, username=None, password=None, secret=None):
    """Add username, password, and secret fields to params dictionary"""
    if username:
        params["username"] = username
    if password:
        params["password"] = password
    if secret:
        params["secret"] = secret
    return params
