from datetime import datetime
import pytest
import time
import re
from netmiko import ReadTimeout

"""
Working traceroute
Failing traceroute
Image transfer of very large file.
show tech-support output        DONE    82 seconds needs a 4 second last_read
show ip bgp output              <don't have a large enough data set>
pinging unreachable destination
pinging 10,000 times to reachable destination   DONE
copying big files on a device
doing a ftp/tftp/http copy initiated on the device
generating ssh keys on a device
generating md5/sha hash for a software image    DONE
failing traceroute that you break out of.
"""

def execute_cmd(
    conn, read_timeout=None, cmd="show tech-support\n", max_loops=None, last_read=2
):
    start_time = datetime.now()
    cmd = cmd.strip()
    conn.write_channel(cmd + "\n")
    if read_timeout is None:
        output = conn.read_channel_timing(
            max_loops=max_loops, last_read=last_read
        )
    else:
        output = conn.read_channel_timing(
            read_timeout=read_timeout, max_loops=max_loops, last_read=last_read
        )
    end_time = datetime.now()
    exec_time = end_time - start_time
    return (output, exec_time)


def my_cleanup(conn, sleep=180):
    try:
        # Must be long enough for "show tech-support" to finish
        time.sleep(sleep)
        conn.disconnect()
    except Exception:
        # If it fails, just try to keep going
        pass



def show_long_running_notimeout(
    conn, read_timeout, cmd="show tech-support\n", last_read=2
):
    """This execution should work i.e. no exception."""
    start_time = datetime.now()
    output = execute_cmd(conn, read_timeout=read_timeout, cmd=cmd, last_read=last_read)
    end_time = datetime.now()
    exec_time = end_time - start_time
    return (output, exec_time)


def test_read_show_tech(net_connect_newconn):

    read_timeout = 0
    output, exec_time = show_long_running_notimeout(
        net_connect_newconn, read_timeout=read_timeout, last_read=4.0
    )
    assert "show interface" in output
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 10


def test_read_md5(net_connect_newconn):

    cmd = "verify /sha512 flash:/c1100-universalk9_ias.16.12.03.SPA.bin\n"
    # cmd = "verify /md5 flash:/c1100-universalk9_ias.16.12.03.SPA.bin\n"
    output, exec_time = show_long_running_notimeout(
        net_connect_newconn, read_timeout=read_timeout, cmd=cmd, last_read=2.0
    )
    assert "Done!" in output
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 10


def test_read_ping(net_connect_newconn):

    cmd = "ping 8.8.8.8 repeat 10000\n"
    output, exec_time = show_long_running_notimeout(
        net_connect_newconn, read_timeout=read_timeout, cmd=cmd, last_read=2.0
    )
    assert "Success rate is" in output
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 10


def test_read_ping_no_resposne(net_connect_newconn):

    # Nothing exists at that IP
    cmd = "ping 10.220.88.209 repeat 10\n"
    output, exec_time = show_long_running_notimeout(
        net_connect_newconn, read_timeout=read_timeout, cmd=cmd, last_read=2.0
    )
    assert "Success rate is" in output
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 10
 
# @pytest.mark.parametrize(
#    "test_timeout,allowed_percentage",
#    [(0.4, 5.0), (1, 2.0), (5, 1.0), (10, 0.5), (60, 0.2)],
# )
# def test_read_timeout(net_connect_newconn, test_timeout, allowed_percentage):
#
#    # Explicitly send expect_string so timing is more accurate
#    my_prompt = net_connect_newconn.find_prompt()
#    pattern = re.escape(my_prompt)
#
#    my_except, exec_time = show_long_running(
#        net_connect_newconn, read_timeout=test_timeout, expect_string=pattern
#    )
#
#    # Returned exception should be read_timeout
#    assert isinstance(my_except, ReadTimeout)
#
#    # Calculate difference in execution time from timeout
#    time_diff = abs(exec_time.total_seconds() - test_timeout)
#    # Convert difference to a percentage of expected timeout
#    time_margin_percent = time_diff / test_timeout * 100
#    # Margin off should be less than the allowed_percentage
#    assert time_margin_percent < allowed_percentage
#
#
# @pytest.mark.parametrize(
#    "test_timeout,allowed_percentage", [(1, 2.0), (5, 1.0), (10, 0.5), (60, 0.2)]
# )
# def test_read_timeout_override(net_connect_newconn, test_timeout, allowed_percentage):
#
#    net_connect_newconn.read_timeout_override = 12
#    ssh_conn = net_connect_newconn
#
#    # Explicitly send expect_string so timing is more accurate
#    my_prompt = net_connect_newconn.find_prompt()
#    pattern = re.escape(my_prompt)
#
#    my_except, exec_time = show_long_running(
#        ssh_conn, read_timeout=test_timeout, expect_string=pattern
#    )
#
#    # Returned exception should be read_timeout
#    assert isinstance(my_except, ReadTimeout)
#
#    # For comparsions compare to the override time with a fixed allowed percentage
#    test_timeout = ssh_conn.read_timeout_override
#    allowed_percentage = 0.5
#
#    # Calculate difference in execution time from read_timeout_override
#    time_diff = abs(exec_time.total_seconds() - test_timeout)
#
#    # Convert difference to a percentage of expected timeout
#    time_margin_percent = time_diff / test_timeout * 100
#    # Margin off should be less than the allowed_percentage
#    assert time_margin_percent < allowed_percentage
#
#
# def test_deprecation_max_loops(net_connect_newconn):
#
#    nc = net_connect_newconn
#    cmd = "show ip int brief"
#    with pytest.deprecated_call():
#        execute_cmd(nc, pattern=r"#", read_timeout=10, cmd=cmd, max_loops=1000)
