#!/bin/bash

for i in `seq 1 10`; do
#    ./test_arista.sh
    py.test -s -v test_netmiko_config.py --test_device arista_sw4
done
