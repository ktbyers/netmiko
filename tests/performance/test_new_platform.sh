#!/bin/sh

export PYTHONPATH=/home/kbyers/netmiko/tests
export TEST_DEVICES=new_devices.yml

pip show netmiko
if [ $? -eq 0 ]; then
    echo
    echo "Verifying that netmiko is not installed ... [FAIL]"
    echo "Uninstall netmiko pacage before running this script."
    exit 1
else
    echo
    echo "Verifying that netmiko is not installed ... [OK]"

fi

vers=$(git tag -l)

for v in $vers
do 
	if [ "$v" \> "v2.4.1" ]; then
		echo "Testing version $v"
		pip install netmiko==$v
		pip show netmiko
		py.test -s test_netmiko.py
		result=$?
		pip uninstall netmiko -y
		if [ $result -eq 0 ]; then
    			echo
    			echo "Running performance tests ... [OK]"
    			echo
		else
    			echo
    			echo "Running performance tests ... [FAIL]"
    			echo "Ensure that your current directory is {NETMIKO_REPO}/tests/performance"
    			exit 1
		fi
	fi

done

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
