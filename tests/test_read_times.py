from datetime import datetime
import pytest
from netmiko import ConnectHandler
from netmiko.utilities import f_exec_time
from netmiko import ReadTimeout


@f_exec_time
def show_long_running(conn, read_timeout):
    start_time = datetime.now()
    my_exception = None
    try:
        output = conn.send_command(
            "show tech-support", read_timeout=read_timeout, expect_string=r"cisco5#"
        )
    except Exception as e:
        my_exception = e
    finally:
        end_time = datetime.now()
        exec_time = end_time - start_time
        print(f"\n\nExec time: {exec_time}\n\n")
        return (my_exception, exec_time)


@pytest.mark.parametrize(
    "test_timeout,allowed_percentage",
    [(0.4, 4.0), (1, 2.0), (5, 1.0), (10, 0.5), (60, 0.2)],
)
def test_read_timeout(test_timeout, allowed_percentage):
    device = {
        "device_type": "cisco_ios",
        "host": "cisco5.lasthop.io",
        "username": "pyclass",
        "password": "bogus",
    }

    ssh_conn = ConnectHandler(**device)
    my_except, exec_time = show_long_running(ssh_conn, read_timeout=test_timeout)

    # Returned exception should be read_timeout
    assert isinstance(my_except, ReadTimeout)

    # Calculate difference in execution time from timeout
    time_diff = abs(exec_time.total_seconds() - test_timeout)
    # Convert difference to a percentage of expected timeout
    time_margin_percent = time_diff / test_timeout * 100
    # Margin off should be less than the allowed_percentage
    print(f"time_margin_percent: {time_margin_percent}")
    assert time_margin_percent < allowed_percentage

@pytest.mark.parametrize(
    "test_timeout,allowed_percentage",
    [(1, 2.0), (5, 1.0), (10, 0.5), (60, 0.2)],
)
def test_read_timeout_override(test_timeout, allowed_percentage):
    device = {
        "device_type": "cisco_ios",
        "host": "cisco5.lasthop.io",
        "username": "pyclass",
        "password": "bogus",
        # Should override the passed in read_timeout
        "read_timeout_override": 12.0,
    }

    ssh_conn = ConnectHandler(**device)
    my_except, exec_time = show_long_running(ssh_conn, read_timeout=test_timeout)

    # Returned exception should be read_timeout
    assert isinstance(my_except, ReadTimeout)

    # For comparsions compare to the override time with a fixed allowed percentage
    test_timeout = ssh_conn.read_timeout_override
    allowed_percentage = .5

    # Calculate difference in execution time from read_timeout_override
    time_diff = abs(exec_time.total_seconds() - test_timeout)

    # Convert difference to a percentage of expected timeout
    time_margin_percent = time_diff / test_timeout * 100
    # Margin off should be less than the allowed_percentage
    print(f"time_margin_percent: {time_margin_percent}")
    assert time_margin_percent < allowed_percentage


def test_deprecation_delay_factor():
    device = {
        "device_type": "cisco_ios",
        "host": "cisco5.lasthop.io",
        "username": "pyclass",
        "password": "bogus",
    }

    ssh_conn = ConnectHandler(**device)
    cmd = "show ip int brief"
    ssh_conn.send_command(cmd, delay_factor=2)
    with pytest.deprecated_call():
        ssh_conn.send_command(cmd, delay_factor=2)

def test_deprecation_max_loops():
    device = {
        "device_type": "cisco_ios",
        "host": "cisco5.lasthop.io",
        "username": "pyclass",
        "password": "bogus",
    }

    ssh_conn = ConnectHandler(**device)
    cmd = "show ip int brief"
    ssh_conn.send_command(cmd, delay_factor=2)
    with pytest.deprecated_call():
        ssh_conn.send_command(cmd, max_loops=1000)
