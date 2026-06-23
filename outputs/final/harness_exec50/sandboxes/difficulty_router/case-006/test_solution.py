from solution import unique_preserve


def test_unique_preserves_order():
    assert unique_preserve(['b', 'a', 'b']) == ['b', 'a']
