#!/bin/sh

export PYTHONPATH=/home/kbyers/netmiko/tests
cd /home/vera/netmiko/tests/performance

pip install pyaml pygal jinja2
if [ $? -eq 0 ]; then
    echo
    echo "Installing dependencies ... [OK]"
    echo
else
    echo
    echo "Installing dependencies ... [FAIL]"
    exit 1
fi

py.test -s test_netmiko.py
if [ $? -eq 0 ]; then
    echo
    echo "Running performance tests ... [OK]"
    echo
else
    echo
    echo "Running performance tests ... [FAIL]"
    exit 1
fi

python gen_graph.py
if [ $? -eq 0 ]; then
    echo
    echo "Generating graphs ... [OK]"
    echo
else
    echo
    echo "Generating graphs ... [FAIL]"
    exit 1
fi
