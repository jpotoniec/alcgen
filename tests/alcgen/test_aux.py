from alcgen.aux import insert_maximal


def test_insert_maximal():
    l = []
    insert_maximal(l, {1})
    assert l == [{1}]
    insert_maximal(l, {2})
    assert l == [{1}, {2}]
    insert_maximal(l, {1, 3})
    assert l == [{1, 3}, {2}]
    insert_maximal(l, {3})
    assert l == [{1, 3}, {2}]
    insert_maximal(l, {1, 2, 3})
    assert l == [{1, 2, 3}]
