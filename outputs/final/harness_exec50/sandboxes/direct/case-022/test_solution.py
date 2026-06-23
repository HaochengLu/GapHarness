from solution import normalize_phone


def test_normalize_phone_keeps_digits_only():
    assert normalize_phone('(555) 123-0000') == '5551230000'
