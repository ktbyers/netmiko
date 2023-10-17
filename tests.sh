black .
pylama .
mypy ./netmiko
py.test -v -s tests/test_import_netmiko.py
py.test -v -s tests/unit/test_base_connection.py
py.test -v -s tests/unit/test_utilities.py
py.test -v -s tests/unit/test_ssh_autodetect.py
py.test -v -s tests/unit/test_connection.py
py.test -v -s tests/unit/test_entry_points.py 
