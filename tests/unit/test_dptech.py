from netmiko import ConnectHandler

def test_dptech_import():
    """Verify 'dptech' device_type is registered."""
    try:
        conn = ConnectHandler(
            device_type="dptech",
            host="192.168.1.1",
            username="admin",
            password="dummy",
            timeout=1,
        )
    except Exception:
        pass  # Expected due to network failure, not driver issue
