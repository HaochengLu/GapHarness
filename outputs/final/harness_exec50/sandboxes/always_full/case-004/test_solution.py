from solution import parse_bool


def test_parse_bool_accepts_yes():
    assert parse_bool(' YES ')
