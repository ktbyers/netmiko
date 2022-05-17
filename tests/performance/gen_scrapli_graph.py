#!/usr/bin/env python
import os
import pygal
import csv
import yaml
import jinja2
from rich import print
from typing import Dict

from pathlib import Path


netmiko_scrapli_platform = {
    "IOSXEDriver": "cisco_xe",
    "NXOSDriver": "cisco_nxos",
    "IOSXRDriver": "cisco_xr",
    "EOSDriver": "arista_eos",
    "JunosDriver": "juniper_junos",
}


def convert_time(time_str):
    """Convert time_str to seconds (float)."""
    results = time_str.split(":")
    hours, mins, secs = [float(my_time) for my_time in results]
    if hours != 0 or mins != 0:
        raise ValueError("Invalid Time Received")
    return secs


def read_csv(device):
    csv_file = "netmiko_scrapli_performance.csv"
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
        version = entry["version"]
        dot_pos = version.rfind(".")
        minor_version = version[:dot_pos]
        dot_pos += 1
        patch_version = version[dot_pos:]
        current_patch = patches.get(minor_version, "0")
        patches[minor_version] = max(patch_version, current_patch)

    last_versions = [f"{minor}.{patch}" for minor, patch in patches.items()]
    entries = filter(lambda x: x["version"] in last_versions, entries)
    return sorted(entries, key=lambda x: x["version"])


def generate_graph(device_name: str, params: Dict) -> None:
    device = device_name
    title = params["graph"]["title"]
    device_dict = params["device"]
    driver = device_dict.pop("driver")
    device_type = netmiko_scrapli_platform[str(driver)]

    if device_name == "cisco1":
        device_type = "cisco_ios"
    outfile = f"netmiko_scrapli_{device_type}.svg"
    entries = read_csv(device)
    # entries = filter_versions(entries)

    # Create relevant lists
    netmiko_version = "4.1.0"
    netmiko_results = []
    scrapli_version = "2022.1.30.post1"
    scrapli_results = []
    for v in entries:
        if v["version"] == netmiko_version:
            netmiko_results.append(convert_time(v["connect"]))
            netmiko_results.append(convert_time(v["send_command_simple"]))
            netmiko_results.append(convert_time(v["send_config_simple"]))
            netmiko_results.append(convert_time(v["send_config_large_acl"]))
        if v["version"] == scrapli_version:
            scrapli_results.append(convert_time(v["connect"]))
            scrapli_results.append(convert_time(v["send_command_simple"]))
            scrapli_results.append(convert_time(v["send_config_simple"]))
            scrapli_results.append(convert_time(v["send_config_large_acl"]))

    print(netmiko_results)
    print(scrapli_results)

    # Graph It
    line_chart = pygal.Line(include_x_axis=True)
    line_chart.title = title
    line_chart.x_labels = ["Connect", "Show Command", "Simple Config", "Large ACL"]
    line_chart.add(f"Netmiko {netmiko_version}", netmiko_results)
    line_chart.add(f"Scrapli {scrapli_version}", scrapli_results)
    dir_path = Path.cwd() / "graphs_netmiko_scrapli"
    if not dir_path.exists():
        dir_path.mkdir()
    line_chart.render_to_file(str(dir_path / outfile))


perf_report_template = """
# Netmiko-Scrapli Performance Comparison
# Netmiko Version: {{netmiko_version}}
# Scrapli Version: {{scrapli_version}}
{%- for graph in graphs %}
![]({{graph}})\n
{%- endfor %}
"""


def generate_report():
    template = jinja2.Template(perf_report_template)
    graphs_path = Path.cwd() / "graphs_netmiko_scrapli"
    graph_files = [
        "graphs_netmiko_scrapli/" + item.name for item in graphs_path.iterdir()
    ]
    report_file = Path.cwd() / "performance_netmiko_scrapli.md"
    with report_file.open("w") as out_file:
        j2_vars = {}
        j2_vars["graphs"] = graph_files
        j2_vars["netmiko_version"] = "4.1.0"
        j2_vars["scrapli_version"] = "2022.1.30.post1"
        out_file.writelines(template.render(**j2_vars))


if __name__ == "__main__":
    f_name = os.environ.get("TEST_DEVICES", "test_devices_scrapli.yml")
    with open(f_name) as f:
        devices = yaml.safe_load(f)
        for device_name, device in devices.items():
            if "graph" in device:
                generate_graph(device_name, device)
    generate_report()
