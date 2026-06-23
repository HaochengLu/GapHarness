from solution import apply_defaults


def test_apply_defaults_fills_missing_key():
    assert apply_defaults({'port': 8080}, {'host': '127.0.0.1', 'port': 80}) == {'host': '127.0.0.1', 'port': 8080}
