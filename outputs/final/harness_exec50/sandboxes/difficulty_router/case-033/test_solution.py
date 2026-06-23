from solution import valid_port


def test_valid_port_rejects_zero():
    assert not valid_port(0)
    assert valid_port(443)
