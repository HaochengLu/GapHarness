from solution import format_currency


def test_format_currency_two_decimals():
    assert format_currency(3) == '$3.00'
