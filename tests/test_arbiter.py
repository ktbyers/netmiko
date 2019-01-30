

def test_arbiter():
    from netmiko.arbiter import CommandBufferArbiter

    cba = CommandBufferArbiter(
        FakeConnection(),
        bucket_size=10,
    )

    for _ in range(cba.bucket_size):
        assert cba.get_token('') is True
    assert cba.get_token('') is False
    assert cba.get_token('prompt') is True
    assert cba.get_token('') is False

    assert cba.all_output() == "prompt\n"


class FakeConnection:
    @staticmethod
    def line_has_prompt(line):
        return True if line == 'prompt' else False
