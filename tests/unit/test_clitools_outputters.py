import pytest
import json
from pathlib import Path
import netmiko.cli_tools.outputters as outputters


def read_json_file(filename):
    file_path = Path(__file__).parent / filename
    return json.loads(file_path.read_text())


@pytest.fixture
def sample_results():
    return {
        "arista1": json.dumps(read_json_file("arista1.json")),
        "arista2": json.dumps(read_json_file("arista2.json")),
    }


def test_output_raw(sample_results, capsys):
    outputters.output_raw(sample_results)
    captured = capsys.readouterr()
    assert "arista1" in captured.out
    assert "arista2" in captured.out
    assert '"address": "10.220.88.28"' in captured.out
    assert '"address": "10.220.88.29"' in captured.out


def test_output_raw_single_device(capsys):
    single_result = {"arista1": json.dumps(read_json_file("arista1.json"))}
    outputters.output_raw(single_result)
    captured = capsys.readouterr()
    assert "arista1" not in captured.out  # Device name should not be printed for single device
    assert '"address": "10.220.88.28"' in captured.out
    assert '"address": "10.220.88.29"' not in captured.out  # Ensure arista2 data is not present


def test_output_json(sample_results, capsys):
    outputters.output_json(sample_results)
    captured = capsys.readouterr()
    assert "arista1" in captured.out
    assert "arista2" in captured.out
    assert '"address": "10.220.88.28"' in captured.out
    assert '"address": "10.220.88.29"' in captured.out


# @pytest.fixture
# def sample_results():
#    return {
#        "device1": "Output for device1",
#        "device2": "Output for device2"
#    }
#
# @pytest.fixture
# def sample_json_results():
#    return {
#        "device1": json.dumps({"key": "value1"}),
#        "device2": json.dumps({"key": "value2"})
#    }
#
# def test_output_raw(sample_results, capsys):
#    outputters.output_raw(sample_results)
#    captured = capsys.readouterr()
#    assert "device1" in captured.out
#    assert "Output for device1" in captured.out
#    assert "device2" in captured.out
#    assert "Output for device2" in captured.out
#
# def test_output_raw_single_device(capsys):
#    single_result = {"device1": "Output for device1"}
#    outputters.output_raw(single_result)
#    captured = capsys.readouterr()
#    assert "device1" not in captured.out
#    assert "Output for device1" in captured.out
#
# @patch('rich.console.Console.print')
# def test_output_text(mock_print, sample_results):
#    outputters.output_text(sample_results)
#    assert mock_print.call_count >= 2  # At least one call per device
#
# @patch('json.loads')
# @patch('rich.console.Console.print')
# def test_output_json(mock_print, mock_json_loads, sample_json_results):
#    mock_json_loads.side_effect = lambda x: json.loads(x)
#    outputters.output_json(sample_json_results)
#    assert mock_print.call_count >= 2  # At least one call per device
#    assert mock_json_loads.call_count == 2
#
# def test_output_json_raw(sample_json_results, capsys):
#    outputters.output_json(sample_json_results, raw=True)
#    captured = capsys.readouterr()
#    assert "device1" in captured.out
#    assert "device2" in captured.out
#    assert '"key": "value1"' in captured.out
#    assert '"key": "value2"' in captured.out
#
# def test_output_json_invalid_json():
#    invalid_json_results = {"device1": "Not a JSON string"}
#    with pytest.raises(json.decoder.JSONDecodeError):
#        outputters.output_json(invalid_json_results)
#
# def test_output_yaml():
#    # This function is not implemented yet, so we'll just check if it exists
#    assert callable(outputters.output_yaml)
#
# @patch('outputters.output_text')
# def test_output_dispatcher_default(mock_output_text, sample_results):
#    outputters.output_dispatcher("unknown_format", sample_results)
#    mock_output_text.assert_called_once_with(sample_results)
#
# @patch('outputters.output_raw')
# def test_output_dispatcher_raw(mock_output_raw, sample_results):
#    outputters.output_dispatcher("raw", sample_results)
#    mock_output_raw.assert_called_once_with(sample_results)
#
# @patch('outputters.output_json')
# def test_output_dispatcher_json_raw(mock_output_json, sample_results):
#    outputters.output_dispatcher("json_raw", sample_results)
#    mock_output_json.assert_called_once_with(sample_results, raw=True)
#
# @patch('rich.console.Console.print')
# def test_output_failed_devices(mock_print):
#    failed_devices = ["device1", "device2"]
#    outputters.output_failed_devices(failed_devices)
#    assert mock_print.call_count >= 1
#
# def test_output_failed_devices_empty():
#    # Test with an empty list to ensure it doesn't raise any errors
#    outputters.output_failed_devices([])
#
## Test the CUSTOM_THEME
# def test_custom_theme():
#    assert "device_name" in outputters.CUSTOM_THEME.styles
#    assert "border" in outputters.CUSTOM_THEME.styles
#    assert "output" in outputters.CUSTOM_THEME.styles
#    assert "failed_title" in outputters.CUSTOM_THEME.styles
#    assert "failed_device" in outputters.CUSTOM_THEME.styles
#    assert "failed_border" in outputters.CUSTOM_THEME.styles
#
## Test sorting of results
# def test_results_sorting():
#    unsorted_results = {"c": "3", "a": "1", "b": "2"}
#    with patch('outputters.output_text') as mock_output_text:
#        outputters.output_dispatcher("text", unsorted_results)
#        # Check if the first argument passed to output_text is sorted
#        called_results = mock_output_text.call_args[0][0]
#        assert list(called_results.keys()) == ["a", "b", "c"]
