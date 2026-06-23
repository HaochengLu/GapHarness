from solution import group_by


def test_group_by_keeps_all_rows():
    rows = [{'team': 'a', 'id': 1}, {'team': 'a', 'id': 2}]
    assert group_by(rows, 'team') == {'a': rows}
