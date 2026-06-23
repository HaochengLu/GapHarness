from solution import is_anagram


def test_is_anagram_ignores_case_and_spaces():
    assert is_anagram('Dormitory', 'dirty room')
