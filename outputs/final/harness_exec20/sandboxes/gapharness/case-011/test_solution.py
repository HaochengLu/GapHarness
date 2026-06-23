from solution import parse_csv_row


def test_parse_csv_row_trims_cells():
    assert parse_csv_row('a, b ,c') == ['a', 'b', 'c']
