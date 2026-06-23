from solution import parse_iso_date


def test_parse_iso_date():
    assert parse_iso_date('2026-06-23') == {'year': 2026, 'month': 6, 'day': 23}
