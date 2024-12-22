import pytest
import json
from pathlib import Path
import netmiko.cli_tools.outputters as outputters


def read_file(filename):
    file_path = Path(__file__).parent / filename
    return file_path.read_text()


def read_json_file(filename):
    return json.loads(read_file(filename))


@pytest.fixture
def sample_results():
    return {
        "arista1": {
            "json": json.dumps(read_json_file("arista1.json")),
            "raw": read_file("arista1.txt"),
        },
        "arista2": {
            "json": json.dumps(read_json_file("arista2.json")),
            "raw": read_file("arista2.txt"),
        },
    }


def test_output_raw(sample_results, capsys):
    raw_results = {device: data["raw"] for device, data in sample_results.items()}
    outputters.output_raw(raw_results)
    captured = capsys.readouterr()
    assert "arista1" in captured.out
    assert "arista2" in captured.out
    assert (
        "Interface         IP Address            Status           Protocol"
        in captured.out
    )
    assert (
        "Management1       unassigned            admin down       down" in captured.out
    )
    assert "Vlan1             10.220.88.28/24       up               up" in captured.out
    assert "Vlan1             10.220.88.29/24       up               up" in captured.out


def test_output_json(sample_results, capsys):
    json_results = {device: data["json"] for device, data in sample_results.items()}
    outputters.output_json(json_results)
    captured = capsys.readouterr()
    assert "arista1" in captured.out
    assert "arista2" in captured.out
    assert '"address": "10.220.88.28"' in captured.out
    assert '"address": "10.220.88.29"' in captured.out


def test_output_raw_single_device(sample_results, capsys):
    single_result = {"arista1": sample_results["arista1"]["raw"]}
    outputters.output_raw(single_result)
    captured = capsys.readouterr()
    assert "arista1" not in captured.out  # Device name should not be in raw output
    assert (
        "Interface         IP Address            Status           Protocol"
        in captured.out
    )
    assert (
        "Management1       unassigned            admin down       down" in captured.out
    )
    assert "Vlan1             10.220.88.28/24       up               up" in captured.out
    assert "10.220.88.29" not in captured.out  # Ensure arista2 data is not present
