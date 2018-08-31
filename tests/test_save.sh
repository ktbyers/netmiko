py.test -s -v test_netmiko_save.py::test_save_base --test_device cisco881
py.test -s -v test_netmiko_save.py::test_save_base --test_device cisco_s300
py.test -s -v test_netmiko_save.py::test_save_confirm --test_device cisco881
py.test -s -v test_netmiko_save.py::test_save_confirm --test_device cisco_s300
py.test -s -v test_netmiko_save.py::test_save_response --test_device cisco881
py.test -s -v test_netmiko_save.py::test_save_response --test_device cisco_s300
