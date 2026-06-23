from solution import parse_tags


def test_parse_tags_normalizes_and_drops_empty():
    assert parse_tags(' AI, Systems, ,Paper ') == ['ai', 'systems', 'paper']
