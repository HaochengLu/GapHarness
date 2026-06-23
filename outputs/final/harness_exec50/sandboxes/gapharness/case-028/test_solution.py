from solution import mask_email


def test_mask_email_keeps_first_character():
    assert mask_email('alice@example.com') == 'a***@example.com'
