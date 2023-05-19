"""Miscellaneous utility functions."""
from typing import (
    Any,
    AnyStr,
    TypeVar,
    Callable,
    cast,
    Optional,
    Union,
    List,
    Dict,
    Tuple,
)
from typing import TYPE_CHECKING
import re
from glob import glob
import sys
import io
import os
from pathlib import Path
import functools
from datetime import datetime
import importlib.resources as pkg_resources
from textfsm import clitable
from textfsm.clitable import CliTableError
from netmiko import log

# For decorators
F = TypeVar("F", bound=Callable[..., Any])


if TYPE_CHECKING:
    from netmiko.base_connection import BaseConnection
    from os import PathLike

try:
    from ttp import ttp

    TTP_INSTALLED = True

except ImportError:
    TTP_INSTALLED = False

try:
    from genie.conf.base import Device
    from genie.libs.parser.utils import get_parser
    from pyats.datastructures import AttrDict

    GENIE_INSTALLED = True
except ImportError:
    GENIE_INSTALLED = False

try:
    import serial.tools.list_ports

    PYSERIAL_INSTALLED = True
except ImportError:
    PYSERIAL_INSTALLED = False

# Dictionary mapping 'show run' for vendors with different command
SHOW_RUN_MAPPER = {
    "brocade_fos": "configShow",
    "juniper": "show configuration",
    "juniper_junos": "show configuration",
    "extreme": "show configuration",
    "extreme_ers": "show running-config",
    "extreme_exos": "show configuration",
    "extreme_netiron": "show running-config",
    "extreme_nos": "show running-config",
    "extreme_slx": "show running-config",
    "extreme_vdx": "show running-config",
    "extreme_vsp": "show running-config",
    "extreme_wing": "show running-config",
    "ericsson_ipos": "show configuration",
    "hp_comware": "display current-configuration",
    "huawei": "display current-configuration",
    "fortinet": "show full-configuration",
    "checkpoint": "show configuration",
    "cisco_wlc": "show run-config",
    "enterasys": "show running-config",
    "dell_force10": "show running-config",
    "avaya_vsp": "show running-config",
    "avaya_ers": "show running-config",
    "brocade_vdx": "show running-config",
    "brocade_nos": "show running-config",
    "brocade_fastiron": "show running-config",
    "brocade_netiron": "show running-config",
    "alcatel_aos": "show configuration snapshot",
    "cros_mtbr": "show running-config",
}

# Expand SHOW_RUN_MAPPER to include '_ssh' key
new_dict = {}
for k, v in SHOW_RUN_MAPPER.items():
    new_key = k + "_ssh"
    new_dict[k] = v
    new_dict[new_key] = v
SHOW_RUN_MAPPER = new_dict

# Default location of netmiko temp directory for netmiko tools
NETMIKO_BASE_DIR = "~/.netmiko"


def load_yaml_file(yaml_file: Union[str, bytes, "PathLike[Any]"]) -> Any:
    """Read YAML file."""
    try:
        import yaml
    except ImportError:
        sys.exit("Unable to import yaml module.")
    try:
        with io.open(yaml_file, "rt", encoding="utf-8") as fname:
            return yaml.safe_load(fname)
    except IOError:
        sys.exit("Unable to open YAML file")


def load_devices(file_name: Union[str, bytes, "PathLike[Any]", None] = None) -> Any:
    """Find and load .netmiko.yml file."""
    yaml_devices_file = find_cfg_file(file_name)
    return load_yaml_file(yaml_devices_file)


def find_cfg_file(
    file_name: Union[str, bytes, "PathLike[Any]", None] = None
) -> Union[str, bytes, "PathLike[Any]"]:
    """
    Search for netmiko_tools inventory file in the following order:
    NETMIKO_TOOLS_CFG environment variable
    Current directory
    Home directory
    Look for file named: .netmiko.yml or netmiko.yml
    Also allow NETMIKO_TOOLS_CFG to point directly at a file
    """
    if file_name and os.path.isfile(file_name):
        return file_name
    optional_path = os.environ.get("NETMIKO_TOOLS_CFG", "")
    if os.path.isfile(optional_path):
        return optional_path
    search_paths = [optional_path, ".", os.path.expanduser("~")]
    # Filter optional_path if null
    search_paths = [path for path in search_paths if path]
    for path in search_paths:
        files = glob(f"{path}/.netmiko.yml") + glob(f"{path}/netmiko.yml")
        if files:
            return files[0]
    raise IOError(
        ".netmiko.yml file not found in NETMIKO_TOOLS environment variable directory,"
        " current directory, or home directory."
    )


def display_inventory(my_devices: Dict[str, Union[List[str], Dict[str, Any]]]) -> None:
    """Print out inventory devices and groups."""
    inventory_groups = ["all"]
    inventory_devices = []
    for k, v in my_devices.items():
        if isinstance(v, list):
            inventory_groups.append(k)
        elif isinstance(v, dict):
            inventory_devices.append((k, v["device_type"]))

    inventory_groups.sort()
    inventory_devices.sort(key=lambda x: x[0])
    print("\nDevices:")
    print("-" * 40)
    for a_device, device_type in inventory_devices:
        device_type = f"  ({device_type})"
        print(f"{a_device:<25}{device_type:>15}")
    print("\n\nGroups:")
    print("-" * 40)
    for a_group in inventory_groups:
        print(a_group)
    print()


def obtain_all_devices(
    my_devices: Dict[str, Union[List[str], Dict[str, Any]]]
) -> Dict[str, Dict[str, Any]]:
    """Dynamically create 'all' group."""
    new_devices = {}
    for device_name, device_or_group in my_devices.items():
        # Skip any groups
        if not isinstance(device_or_group, list):
            new_devices[device_name] = device_or_group
    return new_devices


def obtain_netmiko_filename(device_name: str) -> str:
    """Create file name based on device_name."""
    _, netmiko_full_dir = find_netmiko_dir()
    return f"{netmiko_full_dir}/{device_name}.txt"


def write_tmp_file(device_name: str, output: str) -> str:
    file_name = obtain_netmiko_filename(device_name)
    with open(file_name, "w") as f:
        f.write(output)
    return file_name


def ensure_dir_exists(verify_dir: str) -> None:
    """Ensure directory exists. Create if necessary."""
    if not os.path.exists(verify_dir):
        # Doesn't exist create dir
        os.makedirs(verify_dir)
    else:
        # Exists
        if not os.path.isdir(verify_dir):
            # Not a dir, raise an exception
            raise ValueError(f"{verify_dir} is not a directory")


def find_netmiko_dir() -> Tuple[str, str]:
    """Check environment first, then default dir"""
    try:
        netmiko_base_dir = os.environ["NETMIKO_DIR"]
    except KeyError:
        netmiko_base_dir = NETMIKO_BASE_DIR
    netmiko_base_dir = os.path.expanduser(netmiko_base_dir)
    if netmiko_base_dir == "/":
        raise ValueError("/ cannot be netmiko_base_dir")
    netmiko_full_dir = f"{netmiko_base_dir}/tmp"
    return (netmiko_base_dir, netmiko_full_dir)


def write_bytes(out_data: AnyStr, encoding: str = "utf-8") -> bytes:
    """Ensure output is properly encoded bytes."""
    if isinstance(out_data, str):
        return out_data.encode(encoding)
    elif isinstance(out_data, bytes):
        return out_data
    msg = f"Invalid value for out_data neither unicode nor byte string: {str(out_data)}"
    raise ValueError(msg)


def check_serial_port(name: str) -> str:
    """returns valid COM Port."""

    if not PYSERIAL_INSTALLED:
        msg = (
            "\npyserial is not installed. Please PIP install pyserial:\n\n"
            "pip install pyserial\n\n"
        )
        raise ValueError(msg)

    try:
        cdc = next(serial.tools.list_ports.grep(name))
        serial_port = cdc[0]
        assert isinstance(serial_port, str)
        return serial_port
    except StopIteration:
        msg = f"device {name} not found. "
        msg += "available devices are: "
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            msg += f"{str(p)},"
        raise ValueError(msg)


def get_template_dir(_skip_ntc_package: bool = False) -> str:
    """
    Find and return the directory containing the TextFSM index file.

    Order of preference is:
    1) Find directory in `NET_TEXTFSM` Environment Variable.
    2) Check for pip installed `ntc-templates` location in this environment.
    3) ~/ntc-templates/ntc_templates/templates.

    If `index` file is not found in any of these locations, raise ValueError

    :return: directory containing the TextFSM index file

    """

    msg = """
Directory containing TextFSM index file not found.

Please set the NET_TEXTFSM environment variable to point at the directory containing your TextFSM
index file.

Alternatively, `pip install ntc-templates` (if using ntc-templates).

"""

    # Try NET_TEXTFSM environment variable
    template_dir = os.environ.get("NET_TEXTFSM")
    if template_dir is not None:
        template_dir = os.path.expanduser(template_dir)
        index = os.path.join(template_dir, "index")
        if not os.path.isfile(index):
            # Assume only base ./ntc-templates specified
            template_dir = os.path.join(template_dir, "templates")

    else:
        # Try 'pip installed' ntc-templates
        try:
            with pkg_resources.path(
                package="ntc_templates", resource="parse.py"
            ) as posix_path:
                # Example: /opt/venv/netmiko/lib/python3.8/site-packages/ntc_templates/templates
                template_dir = str(posix_path.parent.joinpath("templates"))
                # This is for Netmiko automated testing
                if _skip_ntc_package:
                    raise ModuleNotFoundError()

        except ModuleNotFoundError:
            # Finally check in ~/ntc-templates/ntc_templates/templates
            home_dir = os.path.expanduser("~")
            template_dir = os.path.join(
                home_dir, "ntc-templates", "ntc_templates", "templates"
            )

    index = os.path.join(template_dir, "index")
    if not os.path.isdir(template_dir) or not os.path.isfile(index):
        raise ValueError(msg)
    return os.path.abspath(template_dir)


def clitable_to_dict(cli_table: clitable.CliTable) -> List[Dict[str, str]]:
    """Converts TextFSM cli_table object to list of dictionaries."""
    return_list = []
    for row in cli_table:
        temp_dict = {}
        for index, element in enumerate(row):
            temp_dict[cli_table.header[index].lower()] = element
        return_list.append(temp_dict)
    return return_list


def _textfsm_parse(
    textfsm_obj: clitable.CliTable,
    raw_output: str,
    attrs: Dict[str, str],
    template_file: Optional[str] = None,
) -> Union[str, List[Dict[str, str]]]:
    """Perform the actual TextFSM parsing using the CliTable object."""
    tfsm_parse: Callable[..., Any] = textfsm_obj.ParseCmd
    try:
        # Parse output through template
        if template_file is not None:
            tfsm_parse(raw_output, templates=template_file)
        else:
            tfsm_parse(raw_output, attrs)

        structured_data = clitable_to_dict(textfsm_obj)
        if structured_data == []:
            return raw_output
        else:
            return structured_data
    except (FileNotFoundError, CliTableError):
        return raw_output


def get_structured_data_textfsm(
    raw_output: str,
    platform: Optional[str] = None,
    command: Optional[str] = None,
    template: Optional[str] = None,
) -> Union[str, List[Dict[str, str]]]:
    """
    Convert raw CLI output to structured data using TextFSM template.

    You can use a straight TextFSM file i.e. specify "template". If no template is specified,
    then you must use an CliTable index file.
    """
    if platform is None or command is None:
        attrs = {}
    else:
        attrs = {"Command": command, "Platform": platform}

    if template is None:
        if attrs == {}:
            raise ValueError(
                "Either 'platform/command' or 'template' must be specified."
            )
        template_dir = get_template_dir()
        index_file = os.path.join(template_dir, "index")
        textfsm_obj = clitable.CliTable(index_file, template_dir)
        output = _textfsm_parse(textfsm_obj, raw_output, attrs)

        # Retry the output if "cisco_xe" and not structured data
        if platform and "cisco_xe" in platform:
            if not isinstance(output, list):
                attrs["Platform"] = "cisco_ios"
                output = _textfsm_parse(textfsm_obj, raw_output, attrs)
        return output
    else:
        template_path = Path(os.path.expanduser(template))
        template_file = template_path.name
        template_dir_alt = template_path.parents[0]
        # CliTable with no index will fall-back to a TextFSM parsing behavior
        textfsm_obj = clitable.CliTable(template_dir=template_dir_alt)
        return _textfsm_parse(
            textfsm_obj, raw_output, attrs, template_file=template_file
        )


# For compatibility
get_structured_data = get_structured_data_textfsm


def get_structured_data_ttp(raw_output: str, template: str) -> Union[str, List[Any]]:
    """
    Convert raw CLI output to structured data using TTP template.

    You can use a straight TextFSM file i.e. specify "template"
    """
    if not TTP_INSTALLED:
        msg = "\nTTP is not installed. Please PIP install ttp:\n\npip install ttp\n"
        raise ValueError(msg)

    try:
        ttp_parser = ttp(data=raw_output, template=template)
        ttp_parser.parse(one=True)
        result: List[Any] = ttp_parser.result(format="raw")
        return result
    except Exception:
        return raw_output


def run_ttp_template(
    connection: "BaseConnection",
    template: Union[str, bytes, "PathLike[Any]"],
    res_kwargs: Dict[str, Any],
    **kwargs: Any,
) -> Any:
    """
    Helper function to run TTP template parsing.

    :param connection: Netmiko connection object

    :param template: TTP template

    :param res_kwargs: ``**res_kwargs`` arguments for TTP result method

    :param kwargs: ``**kwargs`` for TTP object instantiation
    """
    if not TTP_INSTALLED:
        msg = "\nTTP is not installed. Please PIP install ttp:\n" "pip install ttp\n"
        raise ValueError(msg)

    parser = ttp(template=template, **kwargs)

    # get inputs load for TTP template
    ttp_inputs_load = parser.get_input_load()
    log.debug("run_ttp_template: inputs load - {}".format(ttp_inputs_load))

    # go over template's inputs and collect output from devices
    for template_name, inputs in ttp_inputs_load.items():
        for input_name, input_params in inputs.items():
            method = input_params.get("method", "send_command")
            method_kwargs = input_params.get("kwargs", {})
            commands = input_params.get("commands", None)

            # run sanity checks
            if method not in dir(connection):
                log.warning(
                    "run_ttp_template: '{}' input, unsupported method '{}', skipping".format(
                        input_name, method
                    )
                )
                continue
            elif not commands:
                log.warning(
                    "run_ttp_template: '{}' input no commands to collect, skipping".format(
                        input_name
                    )
                )
                continue

            # collect commands output from device
            out_list = [
                getattr(connection, method)(command_string=command, **method_kwargs)
                for command in commands
            ]
            output = "\n".join(out_list)

            # add collected output to TTP parser object
            parser.add_input(
                data=output, input_name=input_name, template_name=template_name
            )

    # run parsing in single process
    parser.parse(one=True)

    return parser.result(**res_kwargs)


def get_structured_data_genie(
    raw_output: str, platform: str, command: str
) -> Union[str, Dict[str, Any]]:
    if not sys.version_info >= (3, 4):
        raise ValueError("Genie requires Python >= 3.4")

    if not GENIE_INSTALLED:
        msg = (
            "\nGenie and PyATS are not installed. Please PIP install both Genie and PyATS:\n"
            "pip install genie\npip install pyats\n"
        )
        raise ValueError(msg)

    if "cisco" not in platform and "linux" not in platform:
        return raw_output

    genie_device_mapper = {
        "cisco_ios": "ios",
        "cisco_xe": "iosxe",
        "cisco_xr": "iosxr",
        "cisco_nxos": "nxos",
        "cisco_asa": "asa",
        "linux": "linux",
        "f5_linux": "linux",
        "ovs_linux": "linux",
    }

    os = None
    # platform might be _ssh, _telnet, _serial strip that off
    if platform.count("_") > 1:
        base_list = platform.split("_")[:-1]
        base_platform = "_".join(base_list)
    else:
        base_platform = platform

    os = genie_device_mapper.get(base_platform)
    if os is None:
        return raw_output

    # Genie specific construct for doing parsing (based on Genie in Ansible)
    device = Device("new_device", os=os)
    device.custom.setdefault("abstraction", {})
    device.custom["abstraction"]["order"] = ["os"]
    device.cli = AttrDict({"execute": None})
    try:
        # Test whether there is a parser for given command (return Exception if fails)
        get_parser(command, device)
        parsed_output: Dict[str, Any] = device.parse(command, output=raw_output)
        return parsed_output
    except Exception:
        return raw_output


def structured_data_converter(
    raw_data: str,
    command: str,
    platform: str,
    use_textfsm: bool = False,
    use_ttp: bool = False,
    use_genie: bool = False,
    textfsm_template: Optional[str] = None,
    ttp_template: Optional[str] = None,
) -> Union[str, List[Any], Dict[str, Any]]:
    """
    Try structured data converters in the following order: TextFSM, TTP, Genie.

    Return the first structured data found, else return the raw_data as-is.
    """
    command = command.strip()
    if use_textfsm:
        structured_output_tfsm = get_structured_data_textfsm(
            raw_data, platform=platform, command=command, template=textfsm_template
        )
        if not isinstance(structured_output_tfsm, str):
            return structured_output_tfsm

    if use_ttp:
        if ttp_template is None:
            msg = """
The argument 'ttp_template=/path/to/template.ttp' must be set when use_ttp=True
"""
            raise ValueError(msg)
        else:
            structured_output_ttp = get_structured_data_ttp(
                raw_data, template=ttp_template
            )

        if not isinstance(structured_output_ttp, str):
            return structured_output_ttp

    if use_genie:
        structured_output_genie = get_structured_data_genie(
            raw_data, platform=platform, command=command
        )
        if not isinstance(structured_output_genie, str):
            return structured_output_genie
    return raw_data


def select_cmd_verify(func: F) -> F:
    """Override function cmd_verify argument with global setting."""

    @functools.wraps(func)
    def wrapper_decorator(self: "BaseConnection", *args: Any, **kwargs: Any) -> Any:
        if self.global_cmd_verify is not None:
            kwargs["cmd_verify"] = self.global_cmd_verify
        return func(self, *args, **kwargs)

    return cast(F, wrapper_decorator)


def m_exec_time(func: F) -> F:
    @functools.wraps(func)
    def wrapper_decorator(self: Any, *args: Any, **kwargs: Any) -> Any:
        start_time = datetime.now()
        result = func(self, *args, **kwargs)
        end_time = datetime.now()
        method_name = str(func)
        print(f"{method_name}: Elapsed time: {end_time - start_time}")
        return result

    return cast(F, wrapper_decorator)


def f_exec_time(func: F) -> F:
    @functools.wraps(func)
    def wrapper_decorator(*args: Any, **kwargs: Any) -> Any:
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        print(f"Elapsed time: {end_time - start_time}")
        return result

    return cast(F, wrapper_decorator)


def calc_old_timeout(
    max_loops: Optional[int] = None,
    delay_factor: Optional[float] = None,
    loop_delay: float = 0.2,
    old_timeout: int = 100,
) -> float:
    """
    loop_delay is .2 in Netmiko 3.x
    delay_factor would multiple the loop delay
    Number of loops was typically 500

    Thus each loop would sleep (loop_delay * delay_factor) seconds
    That sleep would happen max_loops time

    Formula is (loop_delay * delay_factor) * max_loops

    There was a way Netmiko's self.timeout could override the default settings and essentially be
    used to adjust max_loops (this was probably rarely used).
    """
    if max_loops is None:
        max_loops = 500
    if delay_factor is None:
        delay_factor = 1.0
    # This is the logic for having self.timeout override max_loops
    if delay_factor == 1 and max_loops == 500:
        max_loops = int(old_timeout / loop_delay)

    return max_loops * loop_delay * delay_factor


def nokia_context_filter(data: str, re_flags: int = re.M) -> str:
    """
    Nokia context from string. Examples:

    (ro)[]

    (ex)[configure router "Base" bgp]

    Converted over to a standalone function for easier unit testing.
    """
    context_pattern = r"^\!?\*?(\((ex|gl|pr|ro)\))?\[.*\]"
    return re.sub(context_pattern, "", data, flags=re_flags)
