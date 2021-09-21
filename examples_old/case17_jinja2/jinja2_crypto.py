#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import jinja2

template_vars = {"isakmp_enable": True, "encryption": "aes", "dh_group": 5}

cfg_template = """

{%- if isakmp_enable %}
crypto isakmp policy 10
 encr {{ encryption }}
 authentication pre-share
 group {{ dh_group }}
crypto isakmp key my_key address 1.1.1.1 no-xauth
crypto isakmp keepalive 10 periodic
{%- endif %}

"""

template = jinja2.Template(cfg_template)
print(template.render(template_vars))
