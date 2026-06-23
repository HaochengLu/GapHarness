from solution import word_counts


def test_word_counts_strips_punctuation():
    assert word_counts('Hi, hi!') == {'hi': 2}
