from solution import reserve


def test_reserve_subtracts_requested_quantity():
    assert reserve({'book': 10}, 'book', 3) == {'book': 7}
