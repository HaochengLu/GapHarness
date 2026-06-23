from solution import parse_duration


def test_parse_duration_minutes():
    assert parse_duration('2m') == 120
