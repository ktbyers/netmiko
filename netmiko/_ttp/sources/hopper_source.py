import getpass
from hopper import hopper
import logging

log = logging.getLogger(__name__)

_name_map_ = {"hopper_fun": "hopper"}


def hopper_fun(input_name, **kwargs):
    # get username and password
    if kwargs.get("username", "") == "get_user_input":
        username = input("{}, enter username: ".format(input_name))
    if kwargs.get("password", "") == "get_user_pass":
        password = getpass.getpass("{}, enter password: ".format(input_name))
    kwargs.setdefault("credentials", [])
    kwargs["credentials"].append(
        (
            username,
            password,
        )
    )
    log.info(
        "TTP input hopper_fun: sending - '{}', to - '{}'".format(
            kwargs.get("commands"), kwargs.get("devices")
        )
    )
    # get data from devices
    hopperObj = hopper()
    result = hopperObj.run(**kwargs)
    log.info(
        "TTP input hopper_fun: received output from {} devices".format(
            len(result.keys())
        )
    )
    return list(result.values())