import functools
import itertools
from collections import defaultdict
from typing import Collection

import numpy as np

from alcgen.abox import CAssertion, RAssertion, ABox, PartialRAssertion
from alcgen.aux import insert_maximal, intersection, has_non_empty_intersection
from alcgen.guide import Guide
from alcgen.random_guide import RandomGuide
from alcgen.syntax import CE, AND, OR, NOT, ALL, ANY, BOT, TOP, eq, rename, nnf


def _find_subproblems(all_pairs: list[Collection[tuple[int, int]]], different: Collection[tuple[int, int]]) -> \
        list[set[int]]:
    """
    Returns separate subproblems for the problem of closing aboxes.
    :param all_pairs: A collection of collections of pairs, each collection corresponds to an abox, each pair corresponds to a pair of variables that can be used to close the said abox.
    :param different: Pairs of values that must be different, i.e., any time one of them is in a subproblem, the other must be there as well to maintain correctness.
    :return: Indices of aboxes in all_pairs that must be considered jointly
    """
    diff = defaultdict(list)
    for a, b in different:
        diff[a].append(b)
        diff[b].append(a)
    lhs = set()
    for pairs in all_pairs:
        for p, _ in pairs:
            lhs.add(p)
            if p in diff:
                lhs |= set(diff[p])
    class_to_idx = defaultdict(set)
    idx_to_class = [set() for _ in range(len(all_pairs))]
    for i, pairs in enumerate(all_pairs):
        for p in pairs:
            for x in set(p) & lhs:
                class_to_idx[x].add(i)
                idx_to_class[i].add(x)
                idx_to_class[i].update(diff[x])
                for b in diff[x]:
                    class_to_idx[b].add(i)
    visited = set()
    result = []
    for idx in range(len(all_pairs)):
        if idx in visited:
            continue
        indices = {idx}
        new_classes = set(idx_to_class[idx])
        classes = set()
        while True:
            new_indices = set(itertools.chain(*[class_to_idx[i] for i in new_classes])) - indices
            if len(new_indices) == 0:
                break
            classes.update(new_classes)
            new_classes = set(itertools.chain(*[idx_to_class[i] for i in new_indices])) - classes
            indices.update(new_indices)
        visited |= indices
        result.append(indices)
    return result


# TODO controllabel distance between the clashing variables


class Generator:
    _definitions: list[CE | None]
    _different: set[tuple[int, int]]
    _blocked: list[bool]

    def __init__(self, gen: Guide):
        self.gen = gen
        self.n_roles = 0
        self.n_individuals = 0
        self._definitions = []
        self._different = set()
        self._blocked = []

    def _reset(self):
        self.n_roles = 0
        self.n_individuals = 0
        self._definitions.clear()
        self._different.clear()
        self._blocked.clear()

    def _new_class(self) -> int:
        self._definitions.append(None)
        self._blocked.append(False)
        return len(self._definitions) - 1

    def _new_individual(self) -> int:
        i = self.n_individuals
        self.n_individuals += 1
        return i

    def _new_role(self) -> int:
        i = self.n_roles
        self.n_roles += 1
        return i

    def _atomic_classes(self, blocked: bool) -> list[int]:
        return [i for i, c in enumerate(self._definitions) if c is None and (blocked or not self._blocked[i])]

    def _define(self, a: int, def_: CE):
        assert self._definitions[a] is None
        self._definitions[a] = def_

    def _undefine(self, a: int):
        self._definitions[a] = None

    def _is_atomic(self, a: int) -> bool:
        return self._definitions[a] is None

    def _and(self, aboxes: list[ABox], a: int | None = None) -> list[ABox] | None:
        candidates = self._atomic_classes(False)
        if a is None:
            a = self.gen.select_class(candidates)
        else:
            assert a in candidates
        b = self._new_class()
        c = self._new_class()
        self._define(a, (AND, b, c))
        self._different.add((b, c))
        result = []
        for abox in aboxes:
            assertions = set()
            fresh = set()
            for ca in abox.c_assertions:
                if ca.c == a:
                    fresh.add(CAssertion(b, ca.i))
                    fresh.add(CAssertion(c, ca.i))
                else:
                    assertions.add(ca)
            if len(fresh) > 0:
                result.append(ABox(frozenset(assertions | fresh), abox.r_assertions, frozenset(fresh), abox.forbidden))
            else:
                result.append(abox)
        return result

    def _or_candidates(self, aboxes: list[ABox]) -> list[int]:
        candidates = []
        for c in self._atomic_classes(True):
            relevant = [abox for abox in aboxes if abox.has_class(c)]
            abox_classes = [[abox.classes_of_individual(i) - {c} for i in abox.individuals_of_class(c)] for abox in
                            relevant]
            if len(abox_classes) == 0:
                continue
            th = 2 * len(relevant)
            all_classes = set(itertools.chain(*itertools.chain(*abox_classes)))
            if len(all_classes) < th:
                continue
            different = []
            for d in self._different:
                d = set(d)
                if not (d <= all_classes):
                    continue
                if all(len(s & d) == 0 or d <= s for s in itertools.chain(*abox_classes)):
                    m = max(d)
                    all_classes.remove(m)
                    if len(all_classes) < th:
                        break
                    for classes_list in abox_classes:
                        for classes in classes_list:
                            if m in classes:
                                classes.remove(m)
                elif any(d <= s for s in itertools.chain(*abox_classes)):
                    different.append(d)
            if len(all_classes) < th:
                continue
            for p in itertools.product(*abox_classes):
                common = intersection(p)
                if len(common) < th:
                    continue
                for d in different:
                    if d <= common:
                        common.remove(max(d))
                        if len(common) < th:
                            break
                if len(common) >= th:
                    candidates.append(c)
                    break
        return candidates

    def _or(self, aboxes: list[ABox], a: int | None = None) -> list[ABox] | None:
        candidates = self._or_candidates(aboxes)
        if len(candidates) == 0:
            return None
        if a is None:
            a = self.gen.select_class(candidates)
        else:
            assert a in candidates
        for o in self._atomic_classes(False):
            if o != a:
                self._blocked[o] = True
        b = self._new_class()
        c = self._new_class()
        self._define(a, (OR, b, c))
        self._different.add((b, c))
        result = []
        for abox in aboxes:
            base = set()
            rest = set()
            for ca in abox.c_assertions:
                if ca.c == a:
                    rest.add(ca)
                else:
                    base.add(ca)
            if len(rest) == 0:
                result.append(abox)
                continue
            individuals = [ca.i for ca in rest]
            for classes in itertools.product([b, c], repeat=len(individuals)):
                fresh = {CAssertion(x, i) for x, i in zip(classes, individuals)}
                result.append(ABox(frozenset(base | fresh), abox.r_assertions, frozenset(fresh), abox.forbidden))
        return result

    def _exists_candidates(self, aboxes: list[ABox]) -> list[tuple[int, int]]:
        candidates = []
        if self.n_roles == 0:
            return candidates
        # Find all pairs atomic class - role that are not forbidden in any of the aboxes
        forbidden_r2i = defaultdict(set)
        for abox in aboxes:
            for par in abox.forbidden:
                forbidden_r2i[par.r].add(par.i)
        for a in self._atomic_classes(False):
            a_inds = set(itertools.chain(*[abox.individuals_of_class(a) for abox in aboxes]))
            candidates += [(a, r) for r in range(self.n_roles) if
                           not has_non_empty_intersection(forbidden_r2i[r], a_inds)]
        return candidates

    def _exists(self, aboxes: list[ABox], a: int | None = None, r: int | None = None) -> list[ABox] | None:
        candidates = self._exists_candidates(aboxes)
        if r is not None:
            candidates = [c for c in candidates if c[1] == r and (a is None or c[0] == a)]
            if len(candidates) == 0:
                return None
        if len(candidates) > 0:
            a, r = self.gen.select_class_role_pair(candidates)
        else:
            candidates = self._atomic_classes(False)
            if a is None:
                a = self.gen.select_class(candidates)
            else:
                assert a in candidates
            r = self._new_role()
        # reusing an existing class makes no sense since it will be a new individual anyhow
        b = self._new_class()
        self._define(a, (ANY, r, b))
        result = []
        for abox in aboxes:
            cassertions = set()
            rassertions = set()
            fresh = set()
            for ca in abox.c_assertions:
                if ca.c == a:
                    j = self._new_individual()
                    fresh.add(CAssertion(b, j))
                    rassertions.add(RAssertion(r, ca.i, j))
                else:
                    cassertions.add(ca)
            if len(fresh) > 0:
                result.append(
                    ABox(frozenset(cassertions | fresh), frozenset(abox.r_assertions | rassertions), frozenset(fresh),
                         abox.forbidden))
            else:
                result.append(abox)
        return result

    def _forall_is_suitable(self, abox: ABox, c: int, r: int) -> bool:
        # In every abox it must be either
        relevant_c_i = abox.individuals_of_class(c)
        if len(relevant_c_i) == 0:
            # 1. Not present at all -> i.e., no c at all
            return True
        if has_non_empty_intersection(abox.lfillers_of_role(r), relevant_c_i):
            # 2. Applicable -> i.e., c(i) and r(i, *) for some i
            return True
        # 3. Not applicable (i.e., for all i c(i) => no r(i,*) ), but there's a fresh CA that can slavage the abox
        return any(cb.c != c for cb in abox.fresh)

    def _forall_candidates(self, aboxes: list[ABox]) -> list[tuple[int, int]]:
        ar = list()
        visited = set()
        relevant_aboxes = {}
        for abox in aboxes:
            for ra in abox.r_assertions:
                for c in abox.classes_of_individual(ra.i):
                    if not self._is_atomic(c):
                        continue
                    if self._blocked[c]:
                        continue
                    key = (c, ra.r)
                    if key in visited:
                        continue
                    visited.add(key)
                    if c not in relevant_aboxes:
                        c_relevant_aboxes = relevant_aboxes[c] = [abox for abox in aboxes if abox.has_class(c)]
                    else:
                        c_relevant_aboxes = relevant_aboxes[c]
                    if not all(self._forall_is_suitable(other, c, ra.r) for other in c_relevant_aboxes):
                        continue
                    # All aboxes where the new class expression will be applied must share a class that can be the definer of the newly-introduced symbol
                    ok = True
                    shared_cls = None
                    for abox in c_relevant_aboxes:
                        ind = {rb.f for rb in abox.r_assertions if
                               rb.r == ra.r and rb.i in abox.individuals_of_class(c)}
                        if len(ind) == 0:
                            ok = False
                            break
                        shared_cls = {cb.c for cb in abox.c_assertions if
                                      cb.c != c and cb.i in ind and (shared_cls is None or cb.c in shared_cls)}
                        if len(shared_cls) == 0:
                            ok = False
                            break
                    if not ok:
                        continue
                    ar.append(key)
        return ar

    def _forall(self, aboxes: list[ABox], a: int | None = None, r: int | None = None) -> list[ABox] | None:
        candidates = self._forall_candidates(aboxes)
        if a is not None or r is not None:
            candidates = [ar for ar in candidates if (a is None or ar[0] == a) and (r is None or ar[1] == r)]
        if len(candidates) == 0:
            return None
        a, r = self.gen.select_class_role_pair(candidates)
        b = self._new_class()
        self._define(a, (ALL, r, b))
        result = []
        for abox in aboxes:
            cassertions = set(abox.c_assertions)
            fresh = set()
            forbidden = set()
            is_stale = True
            for i in abox.individuals_of_class(a):
                fresh |= {CAssertion(b, f) for f in abox.rfillers(r, i)}
                forbidden.add(PartialRAssertion(r, i))
                cassertions.remove(CAssertion(a, i))
                is_stale = False
            if not is_stale:
                result.append(ABox(frozenset(cassertions | fresh), frozenset(abox.r_assertions),
                                   frozenset(fresh) if len(fresh) > 0 else abox.fresh & cassertions,
                                   abox.forbidden | forbidden))
            else:
                result.append(abox)
        return result

    def _expand(self, ce: CE) -> CE:
        def aux(ce: CE) -> CE:
            if isinstance(ce, tuple):
                if ce[0] == AND or ce[0] == OR:
                    return ce[0], aux(ce[1]), aux(ce[2])
                elif ce[0] == ANY or ce[0] == ALL:
                    return ce[0], ce[1], aux(ce[2])
                else:
                    assert ce[0] == NOT
                    return NOT, aux(ce[1])
            elif ce == TOP or ce == BOT:
                return ce
            else:
                d = self._definitions[ce]
                if d is None:
                    return ce
                else:
                    return aux(d)

        return nnf(aux(ce))

    def _lonely_assertions(self, aboxes: list[ABox]) -> set[CAssertion]:
        result = set()
        for abox in aboxes:
            for ca in abox.c_assertions:
                if not self._blocked[ca.c] and all(cb == ca or cb.i != ca.i for cb in abox.c_assertions - abox.fresh):
                    result.add(ca)
        return result

    def _lonely_step(self, aboxes: list[ABox]) -> list[ABox] | None:
        lonely = list(self._lonely_assertions(aboxes))
        if len(lonely) > 0:
            # TODO pick at random?
            return self._and(aboxes, lonely[0].c)
        else:
            return None

    def step(self, aboxes: list[ABox]) -> list[ABox] | None:
        rules = [
            self._and,
            self._or,
            self._exists,
            self._forall
        ]
        result = self._lonely_step(aboxes)
        if result is not None:
            return result
        else:
            for rule in self.gen.rule(len(rules)):
                result = rules[rule](aboxes)
                if result is not None:
                    return result
            return None

    def _abox_pairs(self, abox: ABox) -> set[tuple[int, int]]:
        result = set()
        for ca in abox.fresh:
            assert self._is_atomic(ca.c), f"{ca.c} is fresh, but defined as {self._definitions[ca.c]}"
            for cb in abox.classes_of_individual(ca.i):
                # the first variable is always fresh
                if ca.c != cb and (cb, ca.c) not in result:
                    result.add((ca.c, cb))
        return result

    def _pairs(self, aboxes: list[ABox]) -> list[set[tuple[int, int]]]:
        return [self._abox_pairs(abox) for abox in aboxes]

    def _check_different(self, filter: set[int] | None = None) -> bool:
        @functools.cache
        def expand(c):
            return self._expand(c)

        for a, b in self._different:
            if filter is not None and a not in filter and b not in filter:
                continue
            a = expand(a)
            b = expand(b)
            # eq transforms to nnf internally so its fine to expand once
            if eq(a, b) or eq(a, (NOT, b)):
                return False
        return True

    def _is_closed(self, abox: ABox) -> bool:
        for ca in abox.fresh:
            if not self._is_atomic(ca.c):
                if any(c != ca.c and eq(self._expand(ca.c), self._expand((NOT, c))) for c in
                       abox.classes_of_individual(ca.i)):
                    return True
        return False

    def _find_subproblems(self, all_pairs: list[list[tuple[int, int]]]) -> list[set[int]]:
        return _find_subproblems(all_pairs, self._different)

    def _depends_on(self, d: CE | None, b: int) -> bool:
        if d is None:
            return False
        if d == b:
            return True
        if not isinstance(d, tuple):
            return False
        if d[0] == ANY or d[1] == ALL or d[1] == NOT:
            return self._depends_on(d[-1], b)
        else:
            return any(self._depends_on(c, b) for c in d[1:])

    def _close(self, aboxes: list[ABox]) -> bool:
        def helper(idx: int, order: list[int]) -> bool:
            if idx == len(order):
                return True
            abox = aboxes[order[idx]]
            pairs = all_pairs[order[idx]]
            if self._is_closed(abox):
                return helper(idx + 1, order)
            for a, b in pairs:
                if self._definitions[a] is not None:
                    continue
                self._define(a, (NOT, b))
                if self._check_different() and helper(idx + 1, order):
                    return True
                self._undefine(a)
            return False

        assert self._check_different()
        all_pairs = self._pairs(aboxes)
        for subproblem in self._find_subproblems(all_pairs):
            order = sorted(subproblem, key=lambda p: len(all_pairs[p]))
            if not helper(0, order):
                cls = set(itertools.chain(*itertools.chain(*[all_pairs[i] for i in order])))
                print()
                print(self._different)
                print(cls)
                print([self._blocked[c] for c in cls])
                print(*[all_pairs[p] for p in order])
                print(*[abox for abox in aboxes if any(ca.c in cls for ca in abox.fresh)], sep='\n')
                return False
        return True

    def _expand_different(self, a: int, b: int) -> set:
        if self._definitions[a] is not None:
            a = self._definitions[a]
        if self._definitions[b] is not None:
            b = self._definitions[b]
        if isinstance(a, int) and isinstance(b, int):
            return {frozenset([a, b])}
        elif isinstance(a, tuple) and isinstance(b, tuple) and a[0] == b[0]:
            if a[0] == NOT:
                return self._expand_different(a[1], b[1])
            elif a[0] == ANY or a[0] == ALL:
                return self._expand_different(a[2], b[2]) if a[1] == b[1] else set()
            else:
                assert a[0] == AND or a[0] == OR
                # This returns too many constraints as it would suffice for one pair to differ - but it is easier to force both of them
                return self._expand_different(a[1], b[1]) | self._expand_different(a[2], b[2]) | self._expand_different(
                    a[1], b[2]) | self._expand_different(a[2], b[1])
        else:
            return set()

    def minimized(self, aboxes) -> CE:
        unique = []
        for abox in aboxes:
            i2c = defaultdict(set)
            for ca in abox.c_assertions:
                c = self._expand(ca.c)
                if isinstance(c, tuple):
                    assert c[0] == NOT
                    assert isinstance(c[1], int)
                    i2c[ca.i].add(c[1])
                else:
                    i2c[ca.i].add(c)
            for cls in i2c.values():
                insert_maximal(unique, cls)
        for d in self._different:
            # This is an approximation, because it would suffice to one of the constraints to be satisfied
            # But it is much easier to satisfy them all, at the cost of possibly using more symbols
            for x in self._expand_different(*d):
                insert_maximal(unique, x)
        different_than = defaultdict(set)
        mapping = {}
        for batch in unique:
            for u in batch:
                different_than[u] |= batch
        for k, others in different_than.items():
            others.remove(k)
            assert k not in mapping
            used = {mapping[v] for v in others if v in mapping}
            i = 1
            while i in used:
                i += 1
            mapping[k] = i
        return rename(self._expand(0), mapping)

    def run(self, steps: int | None = None, minimize: bool = True) -> CE:
        self._reset()
        c = self._new_class()
        i = self._new_individual()
        current = [ABox(frozenset({CAssertion(c, i)}), frozenset(), frozenset(), frozenset())]
        if steps is None:
            steps = self.gen.steps()
        for _ in range(steps):
            n = self.step(current)
            if n is None:
                break
            current = n
        while True:
            n = self._lonely_step(current)
            if n is None:
                break
            current = n
        closed = self._close(current)
        assert closed
        assert self._check_different()
        if minimize:
            return self.minimized(current)
        else:
            return self._expand(0)
