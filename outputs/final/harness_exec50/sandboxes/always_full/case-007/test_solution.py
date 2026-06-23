from solution import merge_counts


def test_merge_counts_adds_existing_key():
    assert merge_counts({'a': 2}, {'a': 3, 'b': 1}) == {'a': 5, 'b': 1}
