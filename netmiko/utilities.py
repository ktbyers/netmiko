"""Miscellaneous utility functions."""
from glob import glob
import sys
import io
import os
from pathlib import Path
import serial.tools.list_ports
from netmiko._textfsm import _clitable as clitable
from netmiko._textfsm._clitable import CliTableError

try:
    from genie.conf.base import Device
    from genie.libs.parser.utils import get_parser
    from pyats.datastructures import AttrDict

    GENIE_INSTALLED = True
except ImportError:
    GENIE_INSTALLED = False

# Dictionary mapping 'show run' for vendors with different command
SHOW_RUN_MAPPER = {
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


def load_yaml_file(yaml_file):
    """Read YAML file."""
    try:
        import yaml
    except ImportError:
        sys.exit("Unable to import yaml module.")
    try:
        with io.open(yaml_file, "rt", encoding="utf-8") as fname:
            return yaml.safe_load(fname)
    except IOError:
        sys.exit(f"Unable to open YAML file: {yaml_file}")


def load_devices(file_name=None):
    """Find and load .netmiko.yml file."""
    yaml_devices_file = find_cfg_file(file_name)
    return load_yaml_file(yaml_devices_file)


def find_cfg_file(file_name=None):
    """
    Search for netmiko_tools inventory file in the following order:
    NETMIKO_TOOLS_CFG environment variable
    Current directory
    Home directory
    Look for file named: .netmiko.yml or netmiko.yml
    Also allow NETMIKO_TOOLS_CFG to point directly at a file
    """
    if file_name:
        if os.path.isfile(file_name):
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
        ".netmiko.yml file not found in NETMIKO_TOOLS environment variable directory, current "
        "directory, or home directory."
    )


def display_inventory(my_devices):
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


def obtain_all_devices(my_devices):
    """Dynamically create 'all' group."""
    new_devices = {}
    for device_name, device_or_group in my_devices.items():
        # Skip any groups
        if not isinstance(device_or_group, list):
            new_devices[device_name] = device_or_group
    return new_devices


def obtain_netmiko_filename(device_name):
    """Create file name based on device_name."""
    _, netmiko_full_dir = find_netmiko_dir()
    return f"{netmiko_full_dir}/{device_name}.txt"


def write_tmp_file(device_name, output):
    file_name = obtain_netmiko_filename(device_name)
    with open(file_name, "w") as f:
        f.write(output)
    return file_name


def ensure_dir_exists(verify_dir):
    """Ensure directory exists. Create if necessary."""
    if not os.path.exists(verify_dir):
        # Doesn't exist create dir
        os.makedirs(verify_dir)
    else:
        # Exists
        if not os.path.isdir(verify_dir):
            # Not a dir, raise an exception
            raise ValueError(f"{verify_dir} is not a directory")


def find_netmiko_dir():
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


def write_bytes(out_data, encoding="ascii"):
    """Legacy for Python2 and Python3 compatible byte stream."""
    if sys.version_info[0] >= 3:
        if isinstance(out_data, type("")):
            if encoding == "utf-8":
                return out_data.encode("utf-8")
            else:
                return out_data.encode("ascii", "ignore")
        elif isinstance(out_data, type(b"")):
            return out_data
    msg = "Invalid value for out_data neither unicode nor byte string: {}".format(
        out_data
    )
    raise ValueError(msg)


def check_serial_port(name):
    """returns valid COM Port."""
    try:
        cdc = next(serial.tools.list_ports.grep(name))
        return cdc[0]
    except StopIteration:
        msg = f"device {name} not found. "
        msg += "available devices are: "
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            msg += f"{str(p)},"
        raise ValueError(msg)


def get_template_dir():
    """Find and return the ntc-templates/templates dir."""
    try:
        template_dir = os.path.expanduser(os.environ["NET_TEXTFSM"])
        index = os.path.join(template_dir, "index")
        if not os.path.isfile(index):
            # Assume only base ./ntc-templates specified
            template_dir = os.path.join(template_dir, "templates")
    except KeyError:
        # Construct path ~/ntc-templates/templates
        home_dir = os.path.expanduser("~")
        template_dir = os.path.join(home_dir, "ntc-templates", "templates")

    index = os.path.join(template_dir, "index")
    if not os.path.isdir(template_dir) or not os.path.isfile(index):
        msg = """
Valid ntc-templates not found, please install https://github.com/networktocode/ntc-templates
and then set the NET_TEXTFSM environment variable to point to the ./ntc-templates/templates
directory."""
        raise ValueError(msg)
    return os.path.abspath(template_dir)


def clitable_to_dict(cli_table):
    """Converts TextFSM cli_table object to list of dictionaries."""
    objs = []
    for row in cli_table:
        temp_dict = {}
        for index, element in enumerate(row):
            temp_dict[cli_table.header[index].lower()] = element
        objs.append(temp_dict)
    return objs


def _textfsm_parse(textfsm_obj, raw_output, attrs, template_file=None):
    """Perform the actual TextFSM parsing using the CliTable object."""
    try:
        # Parse output through template
        if template_file is not None:
            textfsm_obj.ParseCmd(raw_output, templates=template_file)
        else:
            textfsm_obj.ParseCmd(raw_output, attrs)
        structured_data = clitable_to_dict(textfsm_obj)
        output = raw_output if structured_data == [] else structured_data
        return output
    except (FileNotFoundError, CliTableError):
        return raw_output


def get_structured_data(raw_output, platform=None, command=None, template=None):
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
        return _textfsm_parse(textfsm_obj, raw_output, attrs)
    else:
        template_path = Path(os.path.expanduser(template))
        template_file = template_path.name
        template_dir = template_path.parents[0]
        # CliTable with no index will fall-back to a TextFSM parsing behavior
        textfsm_obj = clitable.CliTable(template_dir=template_dir)
        return _textfsm_parse(
            textfsm_obj, raw_output, attrs, template_file=template_file
        )


def get_structured_data_genie(raw_output, platform, command):
    if not sys.version_info >= (3, 4):
        raise ValueError("Genie requires Python >= 3.4")

    if not GENIE_INSTALLED:
        msg = (
            "\nGenie and PyATS are not installed. Please PIP install both Genie and PyATS:\n"
            "pip install genie\npip install pyats\n"
        )
        raise ValueError(msg)

    if "cisco" not in platform:
        return raw_output

    genie_device_mapper = {
        "cisco_ios": "ios",
        "cisco_xe": "iosxe",
        "cisco_xr": "iosxr",
        "cisco_nxos": "nxos",
        "cisco_asa": "asa",
    }

    os = None
    # platform might be _ssh, _telnet, _serial strip that off
    if platform.count("_") > 1:
        base_platform = platform.split("_")[:-1]
        base_platform = "_".join(base_platform)
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
        # Test of whether their is a parser for the given command (will return Exception if fails)
        get_parser(command, device)
        parsed_output = device.parse(command, output=raw_output)
        return parsed_output
    except Exception:
        return raw_output
