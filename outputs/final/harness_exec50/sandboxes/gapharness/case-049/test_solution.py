from solution import ensure_prefix


def test_ensure_prefix_is_idempotent():
    assert ensure_prefix('gh-123', 'gh-') == 'gh-123'
    assert ensure_prefix('123', 'gh-') == 'gh-123'
