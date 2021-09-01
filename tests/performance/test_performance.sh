#!/bin/sh

py.test -s test_netmiko.py
python gen_graph.py
