from solution import parse_json_lines


def test_parse_json_lines_multiple_rows():
    assert parse_json_lines('{"a": 1}\n{"b": 2}') == [{'a': 1}, {'b': 2}]
