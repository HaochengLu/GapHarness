from solution import redact_token


def test_redact_token_keeps_suffix():
    assert redact_token('token_example_abcdef123456') == 'toke...3456'
