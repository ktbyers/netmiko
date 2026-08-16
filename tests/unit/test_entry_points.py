# ChatGPT generated (and then modified)
import subprocess


def test_entry_points():
    cmds = [
        "netmiko-grep",
        "netmiko-cfg",
        "netmiko-show",
        "netmiko-bulk-encrypt",
    ]
    for cmd in cmds:
        r = subprocess.run(["uv", "run", "--frozen", cmd, "--help"], capture_output=True)
        assert r.returncode == 0
