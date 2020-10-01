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


if __name__ == "__main__":

    csv_file = "netmiko_performance_releases.csv"

    cisco1_entries = []
    with open(csv_file) as f:
        read_csv = csv.DictReader(f)
        for entry in read_csv:
            entry = dict(entry)
            if entry["device_name"] == "cisco1":
                cisco1_entries.append(entry)

    netmiko_versions = [v["netmiko_version"] for v in cisco1_entries]
    connect = [convert_time(v["connect"]) for v in cisco1_entries]
    send_command = [convert_time(v["send_command_simple"]) for v in cisco1_entries]
    send_config = [convert_time(v["send_config_simple"]) for v in cisco1_entries]
    send_config_acl = [convert_time(v["send_config_large_acl"]) for v in cisco1_entries]
    pprint(cisco1_entries)
    print(netmiko_versions)
    print(connect)

    line_chart = pygal.Line(include_x_axis=True)
    line_chart.title = "Netmiko: Cisco IOS Performance"
    line_chart.x_labels = netmiko_versions
    line_chart.add("Connect", connect)
    line_chart.add("Show Command", send_command)
    line_chart.add("Simple Config", send_config)
    line_chart.add("Large ACL", send_config_acl)
    line_chart.render_to_file("netmiko_cisco_ios.svg")
