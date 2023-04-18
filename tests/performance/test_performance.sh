#!/bin/sh

export PYTHONPATH=~/netmiko/tests

pip show pyaml pygal jinja2
if [ $? -eq 0 ]; then
    echo
    echo "Checking dependencies ... [OK]"
    echo
else
    echo
    echo "Checking dependencies ... [FAIL]"
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
    echo "Ensure that your current directory is {NETMIKO_REPO}/tests/performance"
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
    echo "Ensure that your current directory is {NETMIKO_REPO}/tests/performance"
    exit 1
fi
