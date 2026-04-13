import json
import pytest
from pathlib import Path

TEST_ENCRYPTION_KEY = "boguskey"


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


@pytest.fixture
def mixed_results(sample_results):
    """Results with one device having empty output."""
    return {
        "arista1": sample_results["arista1"]["raw"],
        "arista2": "",
    }


@pytest.fixture
def set_encryption_key(monkeypatch):
    """Fixture to set a test encryption key"""

    def _set_key(key=TEST_ENCRYPTION_KEY):
        """Inner function to set a test encryption key"""
        monkeypatch.setenv("NETMIKO_TOOLS_KEY", key)
        return key

    return _set_key
