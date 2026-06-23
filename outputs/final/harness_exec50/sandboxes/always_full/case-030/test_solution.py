from solution import zscores


def test_zscores_zero_variance():
    assert zscores([5, 5, 5]) == [0.0, 0.0, 0.0]
