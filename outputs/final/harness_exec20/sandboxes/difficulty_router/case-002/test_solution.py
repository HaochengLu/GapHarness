from solution import slugify


def test_slugify_lowercases_and_collapses_spaces():
    assert slugify('  Hello   World  ') == 'hello-world'
