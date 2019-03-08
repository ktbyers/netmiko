#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import jinja2

template_file = "ospf_config.j2"
with open(template_file) as f:
    jinja_template = f.read()

ospf_active_interfaces = ["Vlan1", "Vlan2"]
area0_networks = ["10.10.10.0/24", "10.10.20.0/24", "10.10.30.0/24"]
template_vars = {
    "ospf_process_id": 10,
    "ospf_priority": 100,
    "ospf_active_interfaces": ospf_active_interfaces,
    "ospf_area0_networks": area0_networks,
}

template = jinja2.Template(jinja_template)
print(template.render(template_vars))
