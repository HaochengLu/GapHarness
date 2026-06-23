from solution import window_sum


def test_window_sum_all_windows():
    assert window_sum([1, 2, 3, 4], 3) == [6, 9]
