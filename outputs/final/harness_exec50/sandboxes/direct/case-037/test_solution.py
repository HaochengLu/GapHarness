from solution import parse_key_values


def test_parse_key_values_trims_and_skips_blank_lines():
    assert parse_key_values('host = localhost\n\nport= 8080') == {'host': 'localhost', 'port': '8080'}
