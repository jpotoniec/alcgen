from alcgen.aux import insert_maximal, intersection


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


def test_intersection_0():
    assert set() == intersection([])


def test_intersection_1():
    assert {1} == intersection([{1}])


def test_intersection_2():
    assert {2} == intersection([{1, 2}, {2, 3}])


def test_intersection_3():
    assert {1, 2} == intersection([{1, 2, 3, 4}, {1, 2}, {1, 2, 3}])
