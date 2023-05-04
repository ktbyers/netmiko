# ChatGPT generated (and then modified)
import subprocess


def test_entry_points():
    cmds = [
        "netmiko-grep",
        "netmiko-cfg",
        "netmiko-show",
    ]
    for cmd in cmds:
        r = subprocess.run(["poetry", "run", cmd, "--help"], capture_output=True)
        assert r.returncode == 0
