from solution import is_valid_email


def test_email_requires_at_sign():
    assert not is_valid_email('example.com')
