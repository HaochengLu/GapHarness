from solution import parse_int


def test_parse_int_uses_default_for_blank():
    assert parse_int('  ', default=7) == 7
    assert parse_int('42') == 42
