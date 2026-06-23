from solution import clamp


def test_clamp_upper_bound():
    assert clamp(12, 0, 10) == 10
