from solution import dedupe_by_id


def test_dedupe_by_id_keeps_first_record():
    rows = [{'id': 1, 'v': 'a'}, {'id': 1, 'v': 'b'}, {'id': 2, 'v': 'c'}]
    assert dedupe_by_id(rows) == [{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'c'}]
