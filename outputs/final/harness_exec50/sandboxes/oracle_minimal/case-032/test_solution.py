from solution import percent_change


def test_percent_change_zero_baseline():
    assert percent_change(0, 5) is None
