from solution import safe_divide


def test_safe_divide_zero_uses_default():
    assert safe_divide(5, 0, default=None) is None
