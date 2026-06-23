from solution import chunks


def test_chunks_includes_tail():
    assert chunks([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
