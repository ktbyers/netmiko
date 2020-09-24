from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.core.deserializer.inventory import Inventory

import logging

log = logging.getLogger(__name__)

_name_map_ = {"nornir_fun": "nornir"}


def _get_commands_output(task, commands, **kwargs):
    [
        task.run(
            task=netmiko_send_command, command_string=command, name=command, **kwargs
        )
        for command in commands
    ]


def nornir_fun(input_name, **kwargs):
    ret = []
    hosts = kwargs.get("hosts", None)
    if not hosts:
        log.error("ttp.source.nornir: no hosts found")
        return ret
    commands = kwargs.get("commands", None)
    commands = commands if isinstance(commands, list) else [commands]
    if not commands:
        log.error("ttp.source.nornir: no commands found")
        return ret
    netmiko_kwargs = kwargs.get(
        "netmiko_kwargs", {"strip_prompt": False, "strip_command": False}
    )
    num_workers = kwargs.get("num_workers", 100)
    # get username and password
    username = kwargs.get("username", "")
    password = kwargs.get("password", "")
    if username == "get_user_input":
        username = input("{}, enter username: ".format(input_name))
    if password == "get_user_pass":
        import getpass

        password = getpass.getpass("{}, enter password: ".format(input_name))
    for host_data in hosts.values():
        host_data.setdefault("username", username)
        host_data.setdefault("password", password)
    # Initiate Nornir
    nr = InitNornir(
        core={"num_workers": num_workers},
        logging={"enabled": False},
        inventory={"options": {"hosts": hosts}},
    )
    # retrieve commands output
    output = nr.run(task=_get_commands_output, commands=commands, **netmiko_kwargs)
    # form results
    for hostname, results in output.items():
        res = "\n".join([item.result for item in results[1:] if not item.exception])
        if res:
            ret.append(res)
    return ret
