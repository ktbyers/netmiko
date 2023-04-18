#!/usr/bin/env python
import os
import pygal
import csv
import yaml
import jinja2
from pprint import pprint
from typing import Dict

from pathlib import Path


def convert_time(time_str):
    """Convert time_str to seconds (float)."""
    results = time_str.split(":")
    hours, mins, secs = [float(my_time) for my_time in results]
    if hours != 0 or mins != 0:
        raise ValueError("Invalid Time Received")
    return secs


def read_csv(device):
    csv_file = "netmiko_performance.csv"
    entries = []
    with open(csv_file) as f:
        read_csv = csv.DictReader(f)
        for entry in read_csv:
            entry = dict(entry)
            if entry["device_name"] == device:
                entries.append(entry)

    return entries


def filter_versions(entries):
    patches = dict()
    for entry in entries:
        version = entry["netmiko_version"]
        dot_pos = version.rfind(".")
        minor_version = version[:dot_pos]
        dot_pos += 1
        patch_version = version[dot_pos:]
        current_patch = patches.get(minor_version, "0")
        patches[minor_version] = max(patch_version, current_patch)

    last_versions = [f"{minor}.{patch}" for minor, patch in patches.items()]
    entries = filter(lambda x: x["netmiko_version"] in last_versions, entries)
    return sorted(entries, key=lambda x: x["netmiko_version"])


def generate_graph(device_name: str, params: Dict) -> None:
    device = device_name
    title = params["graph"]["title"]
    device_dict = params["device"]
    device_type = device_dict["device_type"]
    outfile = f"netmiko_{device_type}.svg"
    entries = read_csv(device)
    # entries = filter_versions(entries)

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
    dir_path = Path.cwd() / "graphs"
    if not dir_path.exists():
        dir_path.mkdir()
    line_chart.render_to_file(str(dir_path / outfile))


perf_report_template = """
# Netmiko performance
{%- for graph in graphs %}
![]({{graph}})\n
{%- endfor %}
"""


def generate_report():
    template = jinja2.Template(perf_report_template)
    graphs_path = Path.cwd() / "graphs"
    graph_files = ["graphs/" + item.name for item in graphs_path.iterdir()]
    report_file = Path.cwd() / "performance_report.md"
    with report_file.open("w") as out_file:
        out_file.writelines(template.render({"graphs": graph_files}))


if __name__ == "__main__":
    f_name = os.environ.get("TEST_DEVICES", "test_devices.yml")
    with open(f_name) as f:
        devices = yaml.safe_load(f)
        for device_name, device in devices.items():
            if "graph" in device:
                generate_graph(device_name, device)
    generate_report()
