from solution import overlaps


def test_overlaps_detects_intersection():
    assert overlaps((1, 5), (5, 9))
    assert not overlaps((1, 2), (3, 4))
