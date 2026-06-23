from solution import merge_sorted


def test_merge_sorted_keeps_order():
    assert merge_sorted([1, 4], [2, 3]) == [1, 2, 3, 4]
