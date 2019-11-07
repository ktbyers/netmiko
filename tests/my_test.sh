#!/bin/sh
for i in `seq 5` ; do 
    py.test -s -v test_netmiko_scp.py --test_device cisco3 --pdb
    py.test -s -v test_netmiko_show.py --test_device cisco3 --pdb
    py.test -s -v test_netmiko_config.py --test_device cisco3 --pdb
    py.test -s -v test_netmiko_config_acl.py --test_device cisco3 --pdb
    if [ "$?" != "0" ]; then
        break
    fi
done
#    py.test -s -v test_netmiko_show.py --test_device cisco3
#    py.test -s -v test_netmiko_show.py --test_device arista_sw
