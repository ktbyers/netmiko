#!/bin/sh

export PYTHONPATH=/home/kbyers/netmiko/tests
export TEST_DEVICES=new_devices.yml

pip show netmiko
if [ $? -eq 0 ]; then
    echo
    echo "Verifying that netmiko is not installed ... [FAIL]"
    echo "Uninstall netmiko package before running this script."
    exit 1
else
    echo
    echo "Verifying that netmiko is not installed ... [OK]"
fi

vers="2.4.2 3.0.0 3.1.0 3.2.0 3.3.3 3.4.0"
# vers="4.0.0a4"

for v in $vers
do 
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
