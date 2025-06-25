import itertools
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import chain
from typing import TypeVar

import numpy as np

from alcgen.aux import insert_maximal
from alcgen.syntax import CE, AND, OR, NOT, ALL, ANY, to_pretty, BOT, TOP, to_manchester, eq, rename


@dataclass(frozen=True)
class CAssertion:
    c: int
    i: int

    def __repr__(self):
        return f"{self.c}({self.i})"

    def __str__(self):
        return self.__repr__()


@dataclass(frozen=True)
class RAssertion:
    r: int
    i: int
    f: int

    def __repr__(self):
        return f"{self.r}({self.i}, {self.f})"

    def __str__(self):
        return self.__repr__()


@dataclass(frozen=True)
class PartialRAssertion:
    r: int
    i: int


@dataclass(frozen=True)
class ABox:
    c_assertions: frozenset[CAssertion]
    r_assertions: frozenset[RAssertion]
    fresh: frozenset[CAssertion]
    forbidden: frozenset[PartialRAssertion]

    def __repr__(self):
        return "{" + ", ".join(
            [repr(a) + ("*" if a in self.fresh else "") for a in chain(self.c_assertions, self.r_assertions)]) + "}"

    def __str__(self):
        return repr(self)


T = TypeVar('T')


class Guide:
    def __init__(self):
        self.ctr = 0

    def _select(self, items: list[T]) -> T:
        return min(items)

    def select_class(self, classes: list[int]) -> int:
        return self._select(classes)

    def select_role(self, roles: list[int]) -> int:
        return self._select(roles)

    def select_class_role_pair(self, ar: list[tuple[int, int]]):
        return self._select(ar)

    def rule(self, n_rules: int) -> Sequence[int]:
        r = list(range(n_rules))
        r = r[self.ctr + 1:] + r[:self.ctr]
        self.ctr += 1
        return r

    def steps(self) -> int:
        return 5


class RandomGuide(Guide):
    def __init__(self, gen: np.random.Generator, min_steps: int, max_steps: int):
        super().__init__()
        self._gen = gen
        self._min_steps = min_steps
        self._max_steps = max_steps

    def _select(self, items: list[T]) -> T:
        return self._gen.choice(items)

    def rule(self, n_rules: int) -> Sequence[int]:
        return self._gen.permutation(n_rules)

    def steps(self) -> int:
        return self._gen.integers(self._min_steps, self._max_steps)


class Generator3:
    definitions: list[CE | None]
    _different: set[tuple[int, int]]
    _blocked: list[bool]

    def __init__(self, gen: Guide):
        self.gen = gen
        self.n_roles = 0
        self.n_individuals = 0
        self.definitions = []
        self._different = set()
        self._blocked = []

    def _reset(self):
        self.n_roles = 0
        self.n_individuals = 0
        self.definitions.clear()
        self._different.clear()
        self._blocked.clear()

    def _new_class(self) -> int:
        self.definitions.append(None)
        self._blocked.append(False)
        return len(self.definitions) - 1

    def _new_individual(self) -> int:
        i = self.n_individuals
        self.n_individuals += 1
        return i

    def _new_role(self) -> int:
        i = self.n_roles
        self.n_roles += 1
        return i

    def _atomic_classes(self, blocked: bool) -> list[int]:
        return [i for i, c in enumerate(self.definitions) if c is None and (blocked or not self._blocked[i])]

    def _define(self, a: int, def_: CE):
        assert self.definitions[a] is None
        # print(a, ":=", to_pretty(def_))
        self.definitions[a] = def_

    def _undefine(self, a: int):
        self.definitions[a] = None

    def _is_atomic(self, a: int) -> bool:
        return self.definitions[a] is None

    def _and(self, aboxes: list[ABox], a: int | None = None) -> list[ABox] | None:
        if a is None:
            a = self.gen.select_class(self._atomic_classes(False))
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

    def _or(self, aboxes: list[ABox], a: int | None = None) -> list[ABox] | None:
        def intersection(sets: list[set]) -> set:
            assert len(sets) >= 1
            if len(sets) == 1:
                return sets[0]
            return set(sets[0]).intersection(*sets[1:])

        if a is None:
            candidates = []
            for c in self._atomic_classes(True):
                relevant = [abox for abox in aboxes if any(ca.c == c for ca in abox.c_assertions)]
                abox_classes = [[{cb.c for cb in abox.c_assertions if cb.i == i and cb.c != c} for i in
                                 [ca.i for ca in abox.c_assertions if ca.c == c]] for abox in relevant]
                if len(abox_classes) == 0:
                    continue
                if len(set(itertools.chain(*itertools.chain(*abox_classes)))) < 2 * len(relevant):
                    continue
                if any(len(intersection(p)) >= 2 * len(relevant) for p in itertools.product(*abox_classes)):
                    candidates.append(c)

            # print(candidates)
            if len(candidates) == 0:
                return None
            a = self.gen.select_class(candidates)
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
                assert len(individuals) == len(classes)
                fresh = {CAssertion(x, i) for x, i in zip(classes, individuals)}
                result.append(ABox(frozenset(base | fresh), abox.r_assertions, frozenset(fresh), abox.forbidden))
        return result

    def _exists(self, aboxes: list[ABox]) -> list[ABox] | None:
        candidates = []
        if self.n_roles > 0:
            # Find all pairs atomic class - role that are not forbidden in any of the aboxes
            for a in self._atomic_classes(False):
                for r in range(self.n_roles):
                    if not any(ca.c == a and PartialRAssertion(r, ca.i) in abox.forbidden for abox in aboxes for ca in
                               abox.c_assertions):
                        candidates.append((a, r))
        if len(candidates) > 0:
            a, r = self.gen.select_class_role_pair(candidates)
        else:
            a = self.gen.select_class(self._atomic_classes(False))
            # TODO or existing
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

    def _forall(self, aboxes: list[ABox]) -> list[ABox] | None:
        def is_suitable(abox: ABox, ca: CAssertion, ra: RAssertion) -> bool:
            # In every abox it must be either
            relevant_ca = [cb for cb in abox.c_assertions if ca.c == cb.c]
            if len(relevant_ca) == 0:
                # 1. Not present at all -> i.e., no ca.c at all
                return True
            relevant_ra = [rb for rb in abox.r_assertions if ra.r == rb.r]
            if len(relevant_ra) > 0 and any(cb.i == rb.i for cb in relevant_ca for rb in relevant_ra):
                # 2. Applicable -> i.e., ca.c(i) and r(i, *) for some i
                return True
            # 3. Not applicable (i.e., for all i ca.c(i) => no r(i,*) ), but there's a fresh CA that can slavage the abox
            return any(cb.c != ca.c for cb in abox.fresh)

        ar = set()
        visited = set()
        for abox in aboxes:
            for ca in abox.c_assertions:
                if self._is_atomic(ca.c) and not self._blocked[ca.c]:
                    relevant_aboxes = None
                    for ra in abox.r_assertions:
                        if ra.i != ca.i:
                            continue
                        if (ca.c, ra.r) in visited:
                            continue
                        visited.add((ca.c, ra.r))
                        if relevant_aboxes is None:
                            relevant_aboxes = [abox for abox in aboxes if any(cb.c == ca.c for cb in abox.c_assertions)]
                        if not all(is_suitable(other, ca, ra) for other in relevant_aboxes):
                            continue
                        # All aboxes where the new class expression will be applied there must share a class that can be the definer of the newly-introduced symbol
                        ok = True
                        shared_cls = None
                        for abox in relevant_aboxes:
                            ind = {rb.f for rb in abox.r_assertions if
                                   rb.r == ra.r and any(cb.c == ca.c and cb.i == rb.i for cb in abox.c_assertions)}
                            if len(ind) == 0:
                                ok = False
                                break
                            cls = {cb.c for cb in abox.c_assertions if cb.c != ca.c and cb.i in ind}
                            if shared_cls is None:
                                shared_cls = cls
                            else:
                                shared_cls &= cls
                            if len(shared_cls) == 0:
                                ok = False
                                break
                        if not ok:
                            continue
                        ar.add((ca.c, ra.r))
        if len(ar) == 0:
            return None
        a, r = self.gen.select_class_role_pair(list(ar))
        # TODO or existing?
        b = self._new_class()
        self._define(a, (ALL, r, b))
        result = []
        for abox in aboxes:
            cassertions = set(abox.c_assertions)
            fresh = set()
            forbidden = set()
            is_stale = True
            for ca in abox.c_assertions:
                if ca.c == a:
                    for ra in abox.r_assertions:
                        if ra.r == r and ra.i == ca.i:
                            fresh.add(CAssertion(b, ra.f))
                    forbidden.add(PartialRAssertion(r, ca.i))
                    cassertions.remove(ca)
                    is_stale = False
            if not is_stale:
                result.append(ABox(frozenset(cassertions | fresh), frozenset(abox.r_assertions),
                                   frozenset(fresh) if len(fresh) > 0 else abox.fresh & cassertions,
                                   abox.forbidden | forbidden))
            else:
                result.append(abox)
        return result

    def _expand(self, ce: CE) -> CE:
        if isinstance(ce, tuple):
            if ce[0] == AND or ce[0] == OR:
                return ce[0], self._expand(ce[1]), self._expand(ce[2])
            elif ce[0] == ANY or ce[0] == ALL:
                return ce[0], ce[1], self._expand(ce[2])
            else:
                assert ce[0] == NOT
                e = self._expand(ce[1])
                if e == TOP:
                    return BOT
                elif e == BOT:
                    return TOP
                elif isinstance(e, tuple) and e[0] == NOT:
                    return e[1]
                else:
                    return NOT, e
        elif ce == TOP or ce == BOT:
            return ce
        else:
            d = self.definitions[ce]
            if d is None:
                return ce
            else:
                return self._expand(d)

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

    def _pairs(self, aboxes: list[ABox]) -> list[list[tuple[int, int]]]:
        result = []
        for abox in aboxes:
            result.append([])
            for ca in abox.fresh:
                assert self._is_atomic(ca.c), f"{ca.c} is fresh, but defined as {self.definitions[ca.c]}"
                for cb in abox.c_assertions:
                    # this does not guarantee that a variable is always defined or definer - it may vary
                    if ca != cb and ca.i == cb.i and (ca.c < cb.c or cb not in abox.fresh):
                        result[-1].append((ca.c, cb.c))
        return result

    def _check_different(self) -> bool:
        for a, b in self._different:
            if eq(self._expand(a), self._expand(b)) or eq(self._expand(a), self._expand((NOT, b))):
                return False
        return True

    def _is_closed(self, abox: ABox) -> bool:
        for ca in abox.fresh:
            if not self._is_atomic(ca.c):
                for cb in abox.c_assertions:
                    if ca.i == cb.i and eq(self._expand(ca.c), self._expand((NOT, cb.c))):
                        return True
        return False

    def _find_subproblems(self, all_pairs: list[list[tuple[int, int]]]) -> list[set[int]]:
        class_to_idx = defaultdict(set)
        idx_to_class = [set() for _ in range(len(all_pairs))]
        for i, pairs in enumerate(all_pairs):
            for p in pairs:
                for x in p:
                    class_to_idx[x].add(i)
                    idx_to_class[i].add(x)
                    for a, b in self._different:
                        if a == x:
                            class_to_idx[b].add(i)
                            idx_to_class[i].add(b)
                        elif b == x:
                            class_to_idx[a].add(i)
                            idx_to_class[i].add(a)
        visited = set()
        result = []
        for idx in range(len(all_pairs)):
            if idx in visited:
                continue
            indices = {idx}
            while True:
                # TODO this is not particularly effective
                classes = set(itertools.chain(*[idx_to_class[i] for i in indices]))
                new_indices = set(itertools.chain(*[class_to_idx[i] for i in classes]))
                if new_indices == indices:
                    break
                indices = new_indices
            visited |= indices
            result.append(indices)
        return result

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

    # TODO controllabel distance between the clashing variables

    def _close(self, aboxes: list[ABox]) -> bool:
        def helper(idx: int, order: list[int]) -> bool:
            if idx == len(order):
                return True
            abox = aboxes[order[idx]]
            pairs = all_pairs[order[idx]]
            if self._is_closed(abox):
                return helper(idx + 1, order)
            for a, b in pairs:
                if self.definitions[a] is not None:
                    continue
                self._define(a, (NOT, b))
                if self._check_different() and helper(idx + 1, order):
                    return True
                self._undefine(a)
            # print("Retract", idx)
            return False

        def helper2(idx: int, order: list[int]) -> bool:
            stack = [(0, [])]
            while len(stack) > 0:
                idx, definitions = stack.pop()
                for x, y in definitions:
                    self._define(x, y)
                if self._check_different():
                    while idx < len(order) and self._is_closed(aboxes[order[idx]]):
                        idx += 1
                    if idx >= len(order):
                        return True
                    print(f"{idx}/{len(order)}", definitions, all_pairs[order[idx]])
                    for a, b in all_pairs[order[idx]]:
                        if self.definitions[a] is None and not self._depends_on(self.definitions[b], a):
                            stack.append((idx + 1, definitions + [(a, (NOT, b))]))
                        if self.definitions[b] is None and not self._depends_on(self.definitions[a], b):
                            stack.append((idx + 1, definitions + [(b, (NOT, a))]))
                        if self.definitions[a] == (NOT, b) or self.definitions[b] == (NOT, a):
                            stack.append((idx + 1, definitions))
                for x, y in definitions:
                    self._undefine(x)
            return False

        def blah(order):
            tmp = defaultdict(set)
            for idx in order:
                for a, b in all_pairs[idx]:
                    tmp[a].add(b)
            print(tmp)

        assert self._check_different()
        all_pairs = self._pairs(aboxes)
        for subproblem in self._find_subproblems(all_pairs):
            order = sorted(subproblem, key=lambda p: len(all_pairs[p]))
            if not helper(0, order):
                cls = set(itertools.chain(*itertools.chain(*[all_pairs[i] for i in order])))
                print(self._different)
                print(cls)
                print([self._blocked[c] for c in cls])
                print(*[abox for abox in aboxes if any(ca.c in cls for ca in abox.c_assertions)], sep='\n')
                return False
        return True

    def _expand_different(self, a: int, b: int) -> set:
        if self.definitions[a] is not None:
            a = self.definitions[a]
        if self.definitions[b] is not None:
            b = self.definitions[b]
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

    def run(self, minimize: bool = True) -> CE:
        self._reset()
        c = self._new_class()
        i = self._new_individual()
        current = [ABox(frozenset({CAssertion(c, i)}), frozenset(), frozenset(), frozenset())]
        for _ in range(self.gen.steps()):
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
        if minimize:
            return self.minimized(current)
        else:
            return self._expand(0)


def main():
    for i in range(0, 1):
        print(f"i={i}")
        result = Generator3(RandomGuide(np.random.default_rng(0xfeed + 17 * i), 1000, 1001)).run()
        print(to_pretty(result))
        with open("/tmp/a.owl", "wt") as f:
            to_manchester(result, "http://example.com/foo", f)
        print()


if __name__ == '__main__':
    main()
