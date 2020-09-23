#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import jinja2

template_vars = {"vlan_id": 400, "vlan_name": "red400"}

vlan_template = """
vlan {{ vlan_id }}
   name {{ vlan_name }}

"""

template = jinja2.Template(vlan_template)
print(template.render(template_vars))
