for i in 1 2 3 4 5 6 7 8
do 
    py.test -s -x -v test_netmiko_commit.py::test_confirm_delay --test_device cisco_xrv
    if [ $? -ne 0 ]; then
        break
    fi
done
