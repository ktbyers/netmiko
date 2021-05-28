import pygal
import csv
from pprint import pprint


def convert_time(time_str):
    """Convert time_str to seconds (float)."""
    results = time_str.split(":")
    hours, mins, secs = [float(my_time) for my_time in results]
    if hours != 0 or mins != 0:
        raise ValueError("Invalid Time Received")
    return secs


def read_csv(device):
    csv_file = "netmiko_performance_releases.csv"
    entries = []
    with open(csv_file) as f:
        read_csv = csv.DictReader(f)
        for entry in read_csv:
            entry = dict(entry)
            if entry["device_name"] == device:
                entries.append(entry)

    return entries


if __name__ == "__main__":

    cisco1 = {
        "device": "cisco1",
        "title": "Netmiko: Cisco IOS Performance (Cisco 881)",
        "outfile": "netmiko_cisco_ios.svg",
    }
    cisco3 = {
        "device": "cisco3",
        "title": "Netmiko: Cisco IOS-XE Performance (Cisco C1111-4P)",
        "outfile": "netmiko_cisco_xe.svg",
    }
    nxos1 = {
        "device": "nxos1",
        "title": "Netmiko: Cisco NX-OS Performance (nx9k virtual)",
        "outfile": "netmiko_cisco_nxos.svg",
    }
    xr_azure = {
        "device": "cisco_xr_azure",
        "title": "Netmiko: Cisco IOS-XR Performance (cisco IOS-XRv 9000)",
        "outfile": "netmiko_cisco_xr.svg",
    }
    arista1 = {
        "device": "arista1",
        "title": "Netmiko: Arista EOS Performance (vEOS)",
        "outfile": "netmiko_arista_eos.svg",
    }

    test_device = cisco1

    device = test_device["device"]
    title = test_device["title"]
    outfile = test_device["outfile"]
    entries = read_csv(device)

    # Create relevant lists
    netmiko_versions = [v["netmiko_version"] for v in entries]
    connect = [convert_time(v["connect"]) for v in entries]
    send_command = [convert_time(v["send_command_simple"]) for v in entries]
    send_config = [convert_time(v["send_config_simple"]) for v in entries]
    send_config_acl = [convert_time(v["send_config_large_acl"]) for v in entries]
    pprint(entries)
    print(netmiko_versions)
    print(connect)

    # Graph It
    line_chart = pygal.Line(include_x_axis=True)
    line_chart.title = title
    line_chart.x_labels = netmiko_versions
    line_chart.add("Connect", connect)
    line_chart.add("Show Command", send_command)
    line_chart.add("Simple Config", send_config)
    line_chart.add("Large ACL", send_config_acl)
    line_chart.render_to_file(outfile)
