from solution import stem


def test_stem_handles_directories_and_multiple_dots():
    assert stem('/tmp/archive.tar.gz') == 'archive.tar'
