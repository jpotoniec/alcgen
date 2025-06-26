from typing import Sequence, TypeVar

from alcgen.abox import PartialRAssertion, RAssertion
from alcgen.generator import Generator, CAssertion, ABox
from alcgen.guide import Guide
from alcgen.syntax import ANY

_T = TypeVar('_T')


class MockGuide(Guide):
    def __init__(self, rules: list[int], n: int | None = None):
        super().__init__()
        self.rules = rules
        if n is None:
            self.n = len(self.rules)
        else:
            self.n = n

    def _select(self, items: list[_T]) -> _T:
        return min(items)

    def rule(self, n_rules: int) -> Sequence[int]:
        r = self.rules.pop(0)
        assert r < n_rules
        return [r]

    def steps(self) -> int:
        return self.n


def abox(*args) -> ABox:
    c_assertions = set()
    r_assertions = set()
    forbidden = set()
    fresh = set()
    last = None
    for a in args:
        if isinstance(a, tuple):
            if len(a) == 2:
                a = CAssertion(a[0], a[1])
            elif len(a) == 3:
                if a[2] is not None:
                    a = RAssertion(a[0], a[1], a[2])
                else:
                    a = PartialRAssertion(a[0], a[1])
            else:
                assert False
        if isinstance(a, CAssertion):
            c_assertions.add(a)
        elif isinstance(a, RAssertion):
            r_assertions.add(a)
        elif isinstance(a, PartialRAssertion):
            forbidden.add(a)
        elif isinstance(a, str) and a == '*' and last is not None:
            fresh.add(last)
        last = a
    return ABox(frozenset(c_assertions), frozenset(r_assertions), frozenset(fresh), frozenset(forbidden))


def test_and():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    i2 = g._new_individual()
    aboxes = g._and([abox((c0, i0)), abox((c1, i0)), abox((c0, i1), (c0, i2), (c1, i1))])
    assert len(aboxes) == 3
    assert aboxes[0] == abox((2, i0), '*', (3, i0), '*')
    assert aboxes[1] == abox((c1, i0))
    assert aboxes[2] == abox((2, i1), '*', (3, i1), '*', (2, i2), '*', (3, i2), '*', (c1, i1))


def test_or_impossible_lonely_assertion():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._or([abox((c0, i0))])
    assert aboxes is None


def test_or_impossible_only_one_other_assertion():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._or([abox((c0, i0), (c1, i0))])
    assert aboxes is None


def test_or_possible():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._or([abox((c0, i0), (c1, i0), (c2, i0))])
    assert len(aboxes) == 2
    assert aboxes[0] == abox((3, i0), '*', (c1, i0), (c2, i0))
    assert aboxes[1] == abox((4, i0), '*', (c2, i0), (c1, i0))
    assert g._blocked[c1]
    assert g._blocked[c2]


def test_or_impossible_wrong_individuals():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    aboxes = g._or([abox((c0, i0), (c1, i0), (c2, i1))])
    assert aboxes is None


def test_or_impossible_no_common():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    c3 = g._new_class()
    c4 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._or([abox((c0, i0), (c1, i0), (c2, i0)),
                    abox((c0, i0), (c3, i0), (c4, i0)),
                    abox((c1, i0), (c2, i0), (c3, i0)),
                    abox((c1, i0), (c2, i0), (c4, i0))
                    ])
    assert aboxes is None


def test_exists_candidates_no_roles():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    i0 = g._new_individual()
    candidates = g._exists_candidates([abox((c0, i0))])
    assert len(candidates) == 0


def test_exists_candidates1():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    candidates = g._exists_candidates([abox((c0, i0), (c0, i1))])
    assert candidates == [(c0, r0)]


def test_exists_candidates2():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    candidates = g._exists_candidates([abox((c0, i0), (c1, i1))])
    assert candidates == [(c0, r0), (c1, r0)]


def test_exists_candidates3():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    r1 = g._new_role()
    candidates = g._exists_candidates([abox((c0, i0), (c1, i1), (r1, i1, None))])
    assert candidates == [(c0, r0), (c0, r1), (c1, r0)]


def test_exists_new_role():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    aboxes = g._exists([abox((c0, i0), (c1, i0)), abox((c1, i0))])
    assert g.n_roles == 1
    assert len(aboxes) == 2
    assert aboxes[0] == abox((2, 1), '*', (c1, i0), (0, 0, 1))
    assert aboxes[1] == abox((c1, i0))
    assert g._definitions[0] == (ANY, 0, 2)


def test_exists_existing_role():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    aboxes = g._exists([abox((c0, i0), (c1, i1), (r0, i0, i1), (r0, i0, None))])
    assert g.n_roles == 1
    assert len(aboxes) == 1
    assert aboxes[0] == abox((2, 2), '*', (c0, i0), (r0, i0, i1), (r0, i1, 2), (r0, i0, None))
    assert g._definitions[1] == (ANY, r0, 2)

# def test_nothing():
#     ce = Generator(MockGuide([], 3)).run(True)
#     assert ce == (AND, (AND, 1, 2), (AND, (NOT, 2), 3))
#
#
# def test_and():
#     ce = Generator(MockGuide([0], 4)).run(True)
#     assert ce == (AND, (AND, (AND, (3, 2), 1), 2), (AND, 3, 4))
#
#
# def test_or():
#     ce = Generator(MockGuide([1], 4)).run(True)
#     assert ce == (4, (4, (5, (3, 1), (3, 2)), 1), (4, 2, 3))
