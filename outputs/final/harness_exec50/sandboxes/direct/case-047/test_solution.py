from solution import expired


def test_expired_at_ttl_boundary():
    assert expired(5, 10, 5)
