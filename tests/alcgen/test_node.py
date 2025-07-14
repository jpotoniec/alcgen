from alcgen.leaf import Leafs, Leaf
from alcgen.node import Node
from alcgen.syntax import AND, ANY, OR


def test_to_ce():
    n = Node(1, 2)
    assert n.to_ce() == (AND, 1, 2)
    m = Node(3, 4, (1, n))
    assert m.to_ce() == (AND, (AND, 3, 4), (ANY, 1, (AND, 1, 2)))
    l = Node(Node(5), Node(6))
    assert l.to_ce() == (OR, 5, 6)


def test_universal1():
    n = Node((1, Node(1)))
    n.add_universal(1, Node(2))
    assert n.existential[1][0].conjuncts == {1}
    assert n.existential[1][0].all_conjuncts == {1, 2}


def test_universal2():
    u = Node()
    u.add_universal(2, Node(4))
    n = Node((1, Node((2, Node(3)))))
    n.add_universal(1, u)
    # assert n.existential[1][0].existential[2][0].conjuncts == {3, 4}


def test_all_conjuncts1():
    a = Node(3)
    a.add_universal(1, Node(1))
    b = Node(4)
    b.add_universal(1, a)
    c = Node((1, Node(5, (1, Node(6, (1, Node(2)))))))
    c.add_universal(1, b)
    assert c.all_conjuncts == set()
    b1 = next(iter(c.existential[1]))
    assert b1.all_conjuncts == {4, 5}
    c1 = next(iter(b1.existential[1]))
    assert c1.all_conjuncts == {3, 6}


def test_all_conjuncts2():
    a = Node(3)
    a.add_universal(1, Node(1))
    b = Node(4)
    b.add_universal(1, a)
    c = Node()
    c.add_universal(1, b)
    c.add_existential(1, Node(5, (1, Node(6, (1, Node(2))))))
    assert c.all_conjuncts == set()
    b1 = next(iter(c.existential[1]))
    assert b1.all_conjuncts == {4, 5}
    c1 = next(iter(b1.existential[1]))
    assert c1.all_conjuncts == {3, 6}


def test_leafs():
    a = Node()
    a.add_universal(1, Node(1))
    b = Node()
    b.add_universal(1, a)
    c = Node((1, Node((1, Node((1, Node(2)))))))
    c.add_universal(1, b)
    assert c.leafs() == Leafs(4, [Leafs(4, [Leafs(4, [Leafs(None, Leaf({2}, set(), set()), 3)], 3)], 3)], 3)


def test_apply_mapping():
    a = Node(3)
    a.add_universal(1, Node(1))
    b = Node(4)
    b.add_universal(1, a)
    c = Node()
    c.add_universal(1, b)
    c.add_existential(1, Node(5, (1, Node(6, (1, Node(2))))))
    assert c.to_ce() == (4, (7, 1, (4, 5, (7, 1, (4, 6, (7, 1, 2))))), (6, 1, (4, 4, (6, 1, (4, 3, (6, 1, 1))))))
    c.apply_mapping({1: 6, 5: 12})
    assert c.to_ce() == (4, (7, 1, (4, 12, (7, 1, (4, 6, (7, 1, 2))))), (6, 1, (4, 4, (6, 1, (4, 3, (6, 1, 6))))))


def test_symbols():
    a = Node()
    a.add_disjunct(Node(1))
    a.add_disjunct(Node(2))
    n = Node(1, 2, 3, (1, Node(7)), (1, Node(9)))
    n.add_disjunct(Node(4, 5))
    n.add_disjunct(Node(5, 6, (1, Node(8))))
    n.add_universal(1, a)
    assert n.symbols() == [{1, 2, 3, 4, 5, 6}, {7, 1, 2}, {9, 1, 2}, {8}]


def test_leafs2():
    n = Node(1, (1, Node(2)))
    n.add_universal(1, Node(3))
    assert n.leafs() == Leafs(AND, [Leafs(None, Leaf(atoms={2}, shared=set(), linked={3}), 1)], 1)
