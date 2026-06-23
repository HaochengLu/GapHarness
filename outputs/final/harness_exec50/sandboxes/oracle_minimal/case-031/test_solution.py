from solution import nested_get


def test_nested_get_walks_all_keys():
    assert nested_get({'a': {'b': 3}}, ['a', 'b']) == 3
    assert nested_get({'a': {}}, ['a', 'b'], default='x') == 'x'
