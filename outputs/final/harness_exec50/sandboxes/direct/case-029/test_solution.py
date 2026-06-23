from solution import top_k


def test_top_k_returns_largest_values():
    assert top_k([4, 1, 9, 2], 2) == [9, 4]
