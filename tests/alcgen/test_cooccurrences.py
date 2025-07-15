from alcgen.cooccurrences import Cooccurrences


def test_cooccurrences1():
    c = Cooccurrences()
    assert c.to_dict() == {}
    c.add({1, 2, 3})
    assert c.to_dict() == {1: {1, 2, 3}, 2: {1, 2, 3}, 3: {1, 2, 3}}
    c.add({4, 5})
    assert c.to_dict() == {1: {1, 2, 3}, 2: {1, 2, 3}, 3: {1, 2, 3}, 4: {4, 5}, 5: {4, 5}}
    c.add({3, 5})
    print(c.to_list())
    assert c.to_dict() == {1: {1, 2, 3, 4, 5}, 2: {1, 2, 3, 4, 5}, 3: {1, 2, 3, 4, 5}, 4: {1, 2, 3, 4, 5},
                           5: {1, 2, 3, 4, 5}}


def test_dsu():
    c = Cooccurrences()
    c.union_many({1, 2, 3})
    c.union_many({4, 5})
    c.union_many({3, 5})
    print(c.to_list())


def test_dsu_union():
    d = Cooccurrences()
    d.union(1, 2)
    d.union(1, 3)
    assert d.to_list() == [{1, 2, 3}]
    d.union(4, 5)
    assert d.to_list() == [{1, 2, 3}, {4, 5}]
    d.union(3, 6)
    assert d.to_list() == [{1, 2, 3, 6}, {4, 5}]
    d.find(7)
    assert d.to_list() == [{1, 2, 3, 6}, {4, 5}, {7}]
    d.union(5, 8)
    assert d.to_list() == [{1, 2, 3, 6}, {4, 5, 8}, {7}]


def test_dsu_union_many():
    d = Cooccurrences()
    d.union_many({1, 2, 3})
    assert d.to_list() == [{1, 2, 3}]
    d.union_many({4, 5})
    assert d.to_list() == [{1, 2, 3}, {4, 5}]
    d.union_many({3, 6})
    assert d.to_list() == [{1, 2, 3, 6}, {4, 5}]
    d.union_many({7})
    assert d.to_list() == [{1, 2, 3, 6}, {4, 5}, {7}]
    d.union_many({5, 8})
    assert d.to_list() == [{1, 2, 3, 6}, {4, 5, 8}, {7}]
    assert d.has_nonempty_intersection({3}, {2, 4})
    assert not d.has_nonempty_intersection({3}, {4})
    assert not d.has_nonempty_intersection({17}, {3, 4})
