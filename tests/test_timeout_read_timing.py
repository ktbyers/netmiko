from datetime import datetime

"""
DONE    Working traceroute
DONE    Failing traceroute
DONE    show tech-support output
DONE    pinging unreachable destination
DONE    pinging 10,000 times to reachable destination
DONE    generating md5/sha hash for a software image
        failing traceroute that you break out of.
        Image transfer of very large file.
        show ip bgp output
        copying big files on a device
        doing a ftp/tftp/http copy initiated on the device
"""


def execute_cmd(conn, cmd="show tech-support", read_timeout=None, last_read=2.0):
    start_time = datetime.now()
    cmd = cmd.strip()
    conn.write_channel(cmd + "\n")
    if read_timeout is None:
        output = conn.read_channel_timing(last_read=last_read)
    else:
        output = conn.read_channel_timing(
            read_timeout=read_timeout, last_read=last_read
        )
    end_time = datetime.now()
    exec_time = end_time - start_time
    return (output, exec_time)


def test_read_show_tech(net_connect_newconn):

    read_timeout = 0
    output, exec_time = execute_cmd(
        net_connect_newconn, read_timeout=read_timeout, last_read=8.0
    )

    assert "show interface" in output
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 10
    net_connect_newconn.disconnect()


def test_read_md5(net_connect_newconn):

    cmd = "verify /sha512 flash:/c1100-universalk9_ias.16.12.03.SPA.bin\n"
    # cmd = "verify /md5 flash:/c1100-universalk9_ias.16.12.03.SPA.bin\n"
    output, exec_time = execute_cmd(net_connect_newconn, cmd=cmd)
    assert "Done!" in output
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 10
    net_connect_newconn.disconnect()


def test_read_ping(net_connect_newconn):

    cmd = "ping 8.8.8.8 repeat 10000\n"
    output, exec_time = execute_cmd(net_connect_newconn, cmd=cmd)
    assert "Success rate is" in output
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 10
    net_connect_newconn.disconnect()


def test_read_ping_no_response(net_connect_newconn):

    # Nothing exists at that IP
    cmd = "ping 10.220.88.209 repeat 20\n"
    output, exec_time = execute_cmd(
        net_connect_newconn,
        cmd=cmd,
    )
    assert "Success rate is" in output
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 10
    net_connect_newconn.disconnect()


def test_read_traceroute_no_response(net_connect_newconn):

    # Will finish in about 90 seconds
    cmd = "traceroute 8.8.8.8 probe 1"
    output, exec_time = execute_cmd(
        net_connect_newconn,
        cmd=cmd,
        last_read=4.0,
        #    read_timeout=300,
    )
    assert "cisco3#" in output
    assert output.count("*") == 30
    assert exec_time.total_seconds() > 10
    net_connect_newconn.disconnect()


def test_read_traceroute_no_response_full(net_connect_newconn):

    # Will finish in about 4.5 minutes
    cmd = "traceroute 8.8.8.8"
    output, exec_time = execute_cmd(
        net_connect_newconn,
        cmd=cmd,
        last_read=4.0,
        read_timeout=6 * 60,  # allow 6-minutes
    )
    assert "cisco3#" in output
    assert output.count("*") == 90
    assert exec_time.total_seconds() > 100
    net_connect_newconn.disconnect()


def test_read_traceroute(net_connect_newconn):

    cmd = "traceroute 10.220.88.37"
    output, exec_time = execute_cmd(
        net_connect_newconn,
        cmd=cmd,
        last_read=4.0,
    )
    assert "cisco3#" in output
    assert exec_time.total_seconds() > 5
    net_connect_newconn.disconnect()
