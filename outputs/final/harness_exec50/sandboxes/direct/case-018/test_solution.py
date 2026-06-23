from solution import normalize_path


def test_normalize_path_collapses_repeated_separators():
    assert normalize_path('//tmp///repo/') == '/tmp/repo'
