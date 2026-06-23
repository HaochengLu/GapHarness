from solution import average


def test_average_empty_uses_default():
    assert average([], default=None) is None
