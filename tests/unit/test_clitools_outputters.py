import netmiko.cli_tools.outputters as outputters


def test_output_raw(sample_results, capsys):
    raw_results = {device: data["raw"] for device, data in sample_results.items()}
    outputters.output_raw(raw_results)
    captured = capsys.readouterr()
    assert "arista1" in captured.out
    assert "arista2" in captured.out
    assert "Interface         IP Address            Status           Protocol" in captured.out
    assert "Management1       unassigned            admin down       down" in captured.out
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
    assert "Interface         IP Address            Status           Protocol" in captured.out
    assert "Management1       unassigned            admin down       down" in captured.out
    assert "Vlan1             10.220.88.28/24       up               up" in captured.out
    assert "10.220.88.29" not in captured.out  # Ensure arista2 data is not present


def test_hide_empty_raw(mixed_results, capsys):
    outputters.output_dispatcher("raw", mixed_results, hide_empty=True)
    captured = capsys.readouterr()
    assert "Vlan1             10.220.88.28/24" in captured.out  # arista1 content present
    assert "arista2" not in captured.out


def test_hide_empty_text(mixed_results, capsys):
    outputters.output_dispatcher("text", mixed_results, hide_empty=True)
    captured = capsys.readouterr()
    assert "arista1" in captured.out
    assert "arista2" not in captured.out


def test_hide_empty_json(sample_results, capsys):
    json_results = {
        "arista1": sample_results["arista1"]["json"],
        "arista2": "",
    }
    outputters.output_dispatcher("json", json_results, hide_empty=True)
    captured = capsys.readouterr()
    assert "arista1" in captured.out
    assert '"address": "10.220.88.28"' in captured.out  # arista1 JSON content present
    assert "arista2" not in captured.out


def test_hide_empty_false_keeps_empty(mixed_results, capsys):
    outputters.output_dispatcher("raw", mixed_results, hide_empty=False)
    captured = capsys.readouterr()
    assert "arista1" in captured.out
    assert "arista2" in captured.out
