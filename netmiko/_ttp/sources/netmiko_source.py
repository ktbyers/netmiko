import getpass
from netmiko import ConnectHandler
import logging

log = logging.getLogger(__name__)

_name_map_ = {"netmiko_fun": "netmiko"}


def netmiko_fun(input_name, **kwargs):
    results = []
    commands = kwargs.pop("commands")
    devices = kwargs.pop("devices") if "devices" in kwargs else []
    if kwargs.get("host"):
        devices.append(kwargs.pop("host"))
    # get username and password
    if kwargs.get("username", "") == "get_user_input":
        kwargs["username"] = input("{}, enter username: ".format(input_name))
    if kwargs.get("password", "") == "get_user_pass":
        kwargs["password"] = getpass.getpass("{}, enter password: ".format(input_name))
    # construct devices list
    devices_dicts = []
    for device in devices:
        devices_dicts.append(kwargs.copy())
        devices_dicts[-1]["host"] = device
    # run commands
    log.info(
        "TTP input netmiko_fun: sending - '{}', to - '{}'".format(commands, devices)
    )
    for item in devices_dicts:
        output = ""
        net_connect = ConnectHandler(**item)
        for command in commands:
            log.info(
                "TTP input netmiko_fun: sending - '{}', to - '{}'".format(
                    command, item.get("host")
                )
            )
            output += "\n" + net_connect.send_command(
                command, strip_prompt=False, strip_command=False
            )
        results.append(output)
    return results