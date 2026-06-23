from solution import join_url


def test_join_url_avoids_double_slash():
    assert join_url('https://example.com/', '/docs') == 'https://example.com/docs'
