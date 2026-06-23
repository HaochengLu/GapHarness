from solution import page


def test_page_is_one_indexed():
    assert page(['a', 'b', 'c', 'd'], 2, 2) == ['c', 'd']
