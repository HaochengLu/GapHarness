from solution import sort_records


def test_sort_records_by_score_then_name():
    rows = [{'name': 'b', 'score': 1}, {'name': 'a', 'score': 1}, {'name': 'c', 'score': 0}]
    assert sort_records(rows) == [{'name': 'c', 'score': 0}, {'name': 'a', 'score': 1}, {'name': 'b', 'score': 1}]
