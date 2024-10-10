import pytest

TEST_ENCRYPTION_KEY = "boguskey"


@pytest.fixture
def set_encryption_key(monkeypatch):
    """Fixture to set a test encryption key"""

    def _set_key(key=TEST_ENCRYPTION_KEY):
        """Inner function to set a test encryption key"""
        monkeypatch.setenv("NETMIKO_TOOLS_KEY", key)
        return key

    return _set_key
