from solution import moving_average


def test_moving_average_all_windows():
    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]
