from typing import Sequence, TypeVar

import numpy as np

from alcgen.abox import PartialRAssertion, RAssertion
from alcgen.generator import Generator, CAssertion, ABox, _find_subproblems
from alcgen.guide import Guide
from alcgen.random_guide import RandomGuide
from alcgen.syntax import ANY, NOT, TOP, BOT, AND, ALL, CE, OR

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


def test_forall_is_suitable():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    # 1. Not present
    assert g._forall_is_suitable(abox((c0, i0)), c1, r0)
    assert g._forall_is_suitable(abox((r0, i0, i1)), c0, r0)
    # 2. Applicable
    assert not g._forall_is_suitable(abox((c0, i0)), c0, r0)
    assert not g._forall_is_suitable(abox((c0, i1), (r0, i0, i1)), c0, r0)
    assert g._forall_is_suitable(abox((c0, i0), (r0, i0, i1)), c0, r0)
    # 3. Salvagable
    assert not g._forall_is_suitable(abox((c0, i0), (c1, i0)), c0, r0)
    assert g._forall_is_suitable(abox((c0, i0), (c1, i0), '*'), c0, r0)


def test_forall_candidates():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    i2 = g._new_individual()
    r0 = g._new_role()
    assert g._forall_candidates([abox((c0, i0), (r0, i0, i1))]) == []
    assert g._forall_candidates([abox((c0, i0), (c1, i0), (r0, i0, i1))]) == []
    assert g._forall_candidates([abox((c0, i0), (c1, i1), (r0, i0, i1))]) == [(c0, r0)]
    assert g._forall_candidates([abox((c0, i0), (c1, i1), (r0, i0, i1)),
                                 abox((c0, i0), (c2, i1), (r0, i0, i1))
                                 ]) == []
    assert g._forall_candidates([abox((c0, i0), (c1, i1), (r0, i0, i1)),
                                 abox((c0, i0), (c1, i1), (r0, i1, i0))
                                 ]) == []
    assert g._forall_candidates([abox((c0, i0), (c1, i1), (r0, i0, i1)),
                                 abox((c0, i1), (c1, i2), (r0, i1, i2))
                                 ]) == [(c0, r0)]
    assert g._forall_candidates([abox((c0, i0), (c1, i1), (r0, i0, i1)),
                                 abox((c0, i0), (c1, i1), '*')
                                 ]) == []


def test_forall():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    aboxes = g._forall([
        abox((c0, i0), (c1, i1), (r0, i0, i1)),
        abox((c1, i0), '*')
    ])
    assert aboxes == [
        abox((c1, i1), (r0, i0, i1), (2, i1), '*', (r0, i0, None)),
        abox((c1, i0), '*')
    ]
    assert g._definitions[0] == (ALL, r0, 2)


def test_forall_none():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    r0 = g._new_role()
    aboxes = g._forall([abox((c0, i0), (c1, i0), (r0, i0, i1))])
    assert aboxes is None


def test_expand_double_negation():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    g._define(c0, (NOT, (NOT, c1)))
    assert g._expand(c0) == c1


def test_expand_not_top():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    g._define(c0, (NOT, TOP))
    assert g._expand(c0) == BOT


def test_expand_and():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    g._define(c0, (AND, c1, c2))
    g._define(c1, (NOT, c2))
    assert g._expand(c0) == (AND, (NOT, c2), c2)


def test_expand_any():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    c2 = g._new_class()
    r0 = g._new_role()
    g._define(c0, (ANY, r0, c1))
    g._define(c1, (NOT, c2))
    assert g._expand(c0) == (ANY, r0, (NOT, c2))


def test_is_closed():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    assert not g._is_closed(abox((c0, i0), (c1, i0), '*'))
    g._define(c1, (NOT, c0))
    assert g._is_closed(abox((c0, i0), (c1, i0), '*'))
    assert not g._is_closed(abox((c0, i0), (c1, i1), '*'))


def test_abox_pairs():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    i0 = g._new_individual()
    i1 = g._new_individual()
    assert g._abox_pairs(abox((c0, i0), (c1, i0), '*')) == {(c1, c0)}
    assert g._abox_pairs(abox((c0, i0), (c1, i0))) == set()
    assert g._abox_pairs(abox((c0, i0), '*', (c1, i0), '*')) in [{(c0, c1)}, {(c1, c0)}]
    assert g._abox_pairs(abox((c0, i0), '*', (c1, i1), '*')) == set()
    assert g._abox_pairs(abox((c0, i0), '*', (c1, i0), '*', (c0, i1), '*', (c1, i1), '*')) in [{(c0, c1)}, {(c1, c0)}]


def test_check_different():
    g = Generator(MockGuide([]))
    c0 = g._new_class()
    c1 = g._new_class()
    g._define(c0, (NOT, c1))
    assert g._check_different()
    g._different.add((c1, c0))
    assert not g._check_different()


def test_find_subproblems():
    assert _find_subproblems([[(1, 2), (1, 3)], [(4, 5), (6, 7)]], []) == [{0}, {1}]
    assert _find_subproblems([[(1, 2), (1, 3)], [(4, 5), (6, 7)]], [(3, 4)]) == [{0, 1}]
    assert _find_subproblems([[(1, 2)], [(3, 4)], [(5, 6)], [(7, 8)]], []) == [{0}, {1}, {2}, {3}]
    assert _find_subproblems([[(1, 2)], [(3, 4)], [(5, 6)], [(7, 8)]], [(2, 3)]) == [{0, 1}, {2}, {3}]
    assert _find_subproblems([[(1, 2)], [(3, 4)], [(5, 6)], [(7, 8)]], [(2, 3), (4, 5)]) == [{0, 1, 2}, {3}]
    assert _find_subproblems([[(1, 2)], [(3, 4)], [(5, 6)], [(7, 8)]], [(3, 2), (5, 4), (7, 6)]) == [{0, 1, 2, 3}]


def test_find_subproblems2():
    all_pairs = [{(89, 14), (89, 7), (89, 6), (89, 3), (89, 27), (89, 5)},
                 {(90, 14), (90, 27), (90, 7), (90, 6), (90, 3), (90, 5)},
                 {(89, 14), (89, 33), (89, 7), (89, 36), (89, 6), (89, 35), (89, 3), (89, 31), (89, 5), (89, 30)},
                 {(90, 30), (90, 14), (90, 33), (90, 7), (90, 36), (90, 6), (90, 35), (90, 3), (90, 31), (90, 5)},
                 {(104, 23), (104, 7), (104, 52), (104, 26), (104, 6), (104, 27), (104, 3), (104, 48), (104, 25),
                  (104, 22), (104, 24), (104, 5), (104, 40), (104, 46), (104, 14)},
                 {(166, 40), (166, 46), (166, 14), (166, 23), (166, 7), (166, 52), (166, 3), (166, 48), (166, 26),
                  (166, 22), (166, 6), (166, 25), (166, 5), (166, 24), (166, 27)},
                 {(167, 27), (167, 40), (167, 46), (167, 14), (167, 23), (167, 7), (167, 52), (167, 3), (167, 48),
                  (167, 26), (167, 22), (167, 6), (167, 25), (167, 5), (167, 24)},
                 {(103, 5), (103, 27), (103, 40), (103, 46), (103, 24), (103, 14), (103, 23), (103, 7), (103, 52),
                  (103, 3), (103, 48), (103, 26), (103, 22), (103, 6), (103, 25)},
                 {(104, 23), (104, 7), (104, 52), (104, 26), (104, 6), (104, 74), (104, 27), (104, 3), (104, 48),
                  (104, 25), (104, 22), (104, 73), (104, 24), (104, 5), (104, 40), (104, 46), (104, 14)},
                 {(166, 40), (166, 46), (166, 5), (166, 14), (166, 23), (166, 7), (166, 74), (166, 52), (166, 3),
                  (166, 48), (166, 26), (166, 22), (166, 6), (166, 25), (166, 73), (166, 24), (166, 27)},
                 {(167, 27), (167, 40), (167, 46), (167, 14), (167, 23), (167, 7), (167, 74), (167, 52), (167, 3),
                  (167, 48), (167, 26), (167, 73), (167, 6), (167, 22), (167, 25), (167, 5), (167, 24)},
                 {(103, 5), (103, 27), (103, 40), (103, 46), (103, 24), (103, 14), (103, 23), (103, 7), (103, 74),
                  (103, 52), (103, 3), (103, 48), (103, 26), (103, 22), (103, 6), (103, 25), (103, 73)},
                 {(147, 24), (146, 26), (147, 27), (146, 50), (147, 112), (147, 5), (146, 7), (146, 22), (146, 25),
                  (147, 14), (147, 26), (146, 147), (147, 23), (146, 40), (147, 50), (146, 3), (146, 55), (146, 6),
                  (147, 7), (146, 27), (147, 22), (146, 24), (147, 25), (146, 112), (147, 40), (147, 55), (147, 3),
                  (146, 5), (147, 6), (146, 14), (146, 23)},
                 {(160, 158), (161, 158), (160, 161), (160, 159), (161, 159)},
                 {(147, 24), (146, 26), (147, 27), (146, 50), (147, 5), (146, 7), (146, 22), (146, 25), (147, 14),
                  (147, 26),
                  (146, 147), (147, 23), (146, 40), (147, 50), (146, 3), (146, 55), (146, 6), (147, 7), (146, 27),
                  (147, 22),
                  (146, 24), (147, 25), (147, 40), (147, 55), (147, 3), (146, 5), (147, 6), (146, 14), (146, 23)},
                 {(160, 158), (161, 158), (161, 160), (160, 159), (161, 159)},
                 {(125, 23), (125, 7), (125, 26), (125, 55), (125, 6), (125, 3), (125, 25), (125, 22), (125, 5),
                  (125, 50),
                  (125, 40), (125, 24), (125, 27), (125, 14)},
                 {(126, 5), (126, 50), (126, 24), (126, 27), (126, 40), (126, 14), (126, 55), (126, 23), (126, 7),
                  (126, 3),
                  (126, 26), (126, 22), (126, 6), (126, 25)},
                 {(127, 14), (127, 55), (127, 23), (127, 7), (127, 50), (127, 3), (127, 26), (127, 22), (127, 6),
                  (127, 25),
                  (127, 27), (127, 5), (127, 40), (127, 24)},
                 {(128, 40), (128, 24), (128, 14), (128, 55), (128, 23), (128, 7), (128, 3), (128, 26), (128, 50),
                  (128, 6),
                  (128, 22), (128, 25), (128, 27), (128, 5)},
                 {(91, 27), (91, 5), (91, 24), (91, 14), (91, 23), (91, 7), (91, 3), (91, 26), (91, 22), (91, 6),
                  (91, 25)},
                 {(101, 100), (100, 96), (101, 96), (100, 99), (101, 99), (100, 98), (101, 98)},
                 {(104, 23), (104, 26), (104, 35), (104, 7), (104, 25), (104, 22), (104, 31), (104, 40), (104, 46),
                  (104, 52),
                  (104, 6), (104, 3), (104, 24), (104, 30), (104, 33), (104, 36), (104, 48), (104, 5), (104, 14)},
                 {(166, 7), (166, 22), (166, 25), (166, 31), (166, 40), (166, 46), (166, 52), (166, 3), (166, 6),
                  (166, 24),
                  (166, 30), (166, 36), (166, 33), (166, 48), (166, 5), (166, 14), (166, 23), (166, 26), (166, 35)},
                 {(167, 30), (167, 36), (167, 33), (167, 48), (167, 5), (167, 14), (167, 23), (167, 26), (167, 35),
                  (167, 7),
                  (167, 22), (167, 25), (167, 31), (167, 40), (167, 46), (167, 52), (167, 3), (167, 6), (167, 24)},
                 {(103, 24), (103, 30), (103, 36), (103, 33), (103, 48), (103, 5), (103, 14), (103, 23), (103, 26),
                  (103, 35),
                  (103, 7), (103, 22), (103, 25), (103, 31), (103, 40), (103, 46), (103, 52), (103, 3), (103, 6)},
                 {(104, 23), (104, 26), (104, 35), (104, 7), (104, 74), (104, 25), (104, 22), (104, 31), (104, 40),
                  (104, 46),
                  (104, 52), (104, 6), (104, 3), (104, 73), (104, 24), (104, 30), (104, 33), (104, 36), (104, 48),
                  (104, 5),
                  (104, 14)},
                 {(166, 7), (166, 74), (166, 22), (166, 25), (166, 31), (166, 40), (166, 46), (166, 52), (166, 3),
                  (166, 6),
                  (166, 73), (166, 24), (166, 30), (166, 36), (166, 33), (166, 48), (166, 5), (166, 14), (166, 23),
                  (166, 26),
                  (166, 35)},
                 {(167, 30), (167, 36), (167, 33), (167, 48), (167, 5), (167, 14), (167, 23), (167, 26), (167, 35),
                  (167, 7),
                  (167, 74), (167, 22), (167, 25), (167, 31), (167, 40), (167, 46), (167, 52), (167, 3), (167, 6),
                  (167, 73),
                  (167, 24)},
                 {(103, 24), (103, 30), (103, 36), (103, 33), (103, 48), (103, 5), (103, 14), (103, 23), (103, 26),
                  (103, 35),
                  (103, 7), (103, 74), (103, 22), (103, 25), (103, 31), (103, 40), (103, 46), (103, 52), (103, 3),
                  (103, 6),
                  (103, 73)},
                 {(147, 24), (146, 26), (146, 35), (147, 30), (147, 36), (147, 33), (146, 50), (147, 112), (147, 5),
                  (146, 7),
                  (146, 22), (146, 25), (147, 14), (147, 26), (146, 147), (147, 23), (146, 31), (146, 40), (147, 35),
                  (147, 50),
                  (146, 3), (146, 55), (146, 6), (147, 7), (147, 22), (146, 24), (146, 30), (147, 25), (147, 31),
                  (146, 33),
                  (146, 36), (146, 112), (147, 40), (147, 55), (147, 3), (146, 5), (147, 6), (146, 14), (146, 23)},
                 {(160, 158), (161, 158), (161, 160), (160, 159), (161, 159)},
                 {(147, 24), (146, 26), (146, 35), (147, 30), (147, 36), (147, 33), (146, 50), (147, 5), (146, 7),
                  (146, 22),
                  (146, 25), (147, 14), (147, 26), (146, 147), (147, 23), (146, 31), (146, 40), (147, 35), (147, 50),
                  (146, 3),
                  (146, 55), (146, 6), (147, 7), (147, 22), (146, 24), (146, 30), (147, 25), (147, 31), (146, 33),
                  (146, 36),
                  (147, 40), (147, 55), (147, 3), (146, 5), (147, 6), (146, 14), (146, 23)},
                 {(160, 158), (161, 158), (160, 161), (160, 159), (161, 159)},
                 {(125, 23), (125, 7), (125, 36), (125, 26), (125, 55), (125, 6), (125, 35), (125, 3), (125, 25),
                  (125, 22),
                  (125, 31), (125, 5), (125, 50), (125, 40), (125, 24), (125, 30), (125, 14), (125, 33)},
                 {(126, 5), (126, 50), (126, 24), (126, 40), (126, 30), (126, 14), (126, 36), (126, 33), (126, 55),
                  (126, 23),
                  (126, 7), (126, 3), (126, 26), (126, 22), (126, 6), (126, 35), (126, 25), (126, 31)},
                 {(127, 14), (127, 36), (127, 33), (127, 55), (127, 23), (127, 7), (127, 50), (127, 3), (127, 26),
                  (127, 22),
                  (127, 6), (127, 35), (127, 25), (127, 31), (127, 5), (127, 40), (127, 24), (127, 30)},
                 {(128, 40), (128, 24), (128, 30), (128, 14), (128, 36), (128, 33), (128, 55), (128, 23), (128, 7),
                  (128, 3),
                  (128, 26), (128, 22), (128, 6), (128, 35), (128, 50), (128, 25), (128, 31), (128, 5)},
                 {(91, 5), (91, 24), (91, 30), (91, 14), (91, 33), (91, 23), (91, 7), (91, 36), (91, 3), (91, 26),
                  (91, 22),
                  (91, 6), (91, 35), (91, 25), (91, 31)},
                 {(100, 96), (101, 96), (100, 99), (101, 99), (100, 98), (101, 98), (100, 101)},
                 {(162, 142), (162, 7), (162, 3), (162, 6), (162, 5)},
                 {(164, 5), (165, 7), (165, 142), (165, 3), (164, 7), (164, 165), (164, 142), (165, 6), (165, 5),
                  (164, 3),
                  (164, 6)}, {(170, 7), (170, 3), (170, 6), (170, 140), (170, 5)},
                 {(171, 7), (171, 3), (171, 6), (171, 140), (171, 5)}, {(168, 135), (168, 136), (168, 137)},
                 {(169, 135), (169, 136), (169, 137)}, {(130, 7), (130, 3), (130, 5), (130, 6)}]
    different = {(164, 165), (100, 101), (132, 133), (41, 42), (96, 97), (73, 74), (170, 171), (9, 10), (129, 130),
                 (106, 107),
                 (166, 167), (15, 16), (47, 48), (162, 163), (134, 135), (144, 145), (80, 81), (85, 86), (140, 141),
                 (71, 72),
                 (136, 137), (108, 109), (49, 50), (104, 105), (13, 14), (151, 152), (45, 46), (55, 56), (110, 111),
                 (51, 52),
                 (142, 143), (23, 24), (78, 79), (83, 84), (138, 139), (115, 116), (19, 20), (57, 58), (112, 113),
                 (89, 90),
                 (149, 150), (53, 54), (25, 26), (21, 22), (31, 32), (123, 124), (17, 18), (27, 28), (64, 65),
                 (119, 120),
                 (146, 147), (156, 157), (5, 6), (87, 88), (1, 2), (29, 30), (121, 122), (153, 154), (117, 118),
                 (62, 63), (94, 95),
                 (3, 4), (35, 36), (127, 128), (91, 92), (68, 69), (160, 161), (59, 60), (37, 38), (102, 103), (33, 34),
                 (43, 44),
                 (98, 99), (125, 126), (39, 40), (11, 12), (66, 67), (76, 77), (158, 159), (168, 169), (7, 8)}
    subproblems = _find_subproblems(all_pairs, different)
    assert 15 == len(subproblems)


def test_bruteforce():
    def ops(ce: CE) -> set[int]:
        if isinstance(ce, tuple):
            result = {ce[0]}
            for child in ce[1:]:
                result |= ops(child)
            return result
        else:
            return set()

    all_ops = set()
    for i in range(0, 200):
        result = Generator(RandomGuide(np.random.default_rng(0xfeed + 17 * i), 10, 200)).run()
        all_ops |= ops(result)
    assert all_ops == {AND, OR, ANY, ALL, NOT}


def test_90_697():
    seed1: int = 0xbeef
    seed2: int = 0xfeed
    seed3: int = 0xc0ffee
    steps = 90
    i = 697
    guide = RandomGuide(np.random.default_rng(seed1 * steps + seed2 * i + seed3), steps, steps)
    Generator(guide).run(steps)


def test_110_53():
    seed1: int = 0xbeef
    seed2: int = 0xfeed
    seed3: int = 0xc0ffee
    steps = 110
    i = 2
    guide = RandomGuide(np.random.default_rng(seed1 * steps + seed2 * i + seed3), steps, steps)
    Generator(guide).run(steps)

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
