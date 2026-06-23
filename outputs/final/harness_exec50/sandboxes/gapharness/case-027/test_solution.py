from solution import bytes_to_kib


def test_bytes_to_kib_uses_binary_units():
    assert bytes_to_kib(2048) == 2
