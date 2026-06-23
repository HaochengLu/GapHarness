from solution import transpose


def test_transpose_matrix():
    assert transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]
