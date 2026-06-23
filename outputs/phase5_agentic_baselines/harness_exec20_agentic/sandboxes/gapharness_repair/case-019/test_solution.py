from solution import is_palindrome


def test_palindrome_ignores_case_and_spaces():
    assert is_palindrome('Never odd or even')
