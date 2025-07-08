import copy
import itertools
from collections import defaultdict, Counter
from typing import Collection

import numpy as np

from alcgen.syntax import CE, AND, ANY, OR, TOP, to_pretty, ALL, NOT, to_manchester

Model = list[int | tuple[int, "Model"]]


class Node:
    conjuncts: set[int]
    disjuncts: list["Node"]
    existential: dict[int, list["Node"]]
    universal: dict[int, list["Node"]]
    linked: list["Node"]

    def __init__(self, *args):
        self.conjuncts = set()
        self.disjuncts = []
        self.existential = defaultdict(list)
        self.universal = defaultdict(list)
        self.linked = []
        for arg in args:
            if isinstance(arg, Node):
                self.disjuncts.append(arg)
            elif isinstance(arg, tuple):
                assert len(arg) == 2
                self.add_existential(*arg)
            else:
                self.add_conjunct(arg)

    def to_ce(self) -> CE:
        def _join(op, items):
            result = None
            for item in items:
                if not isinstance(item, tuple) and item < 0:
                    item = (NOT, -item)
                if result is None:
                    result = item
                else:
                    result = (op, result, item)
            return result

        conjuncts = itertools.chain(self.conjuncts,
                                    [(ANY, r, n.to_ce()) for r, nodes in self.existential.items() for n in
                                     nodes],
                                    [(ALL, r, n.to_ce()) for r, nodes in self.universal.items() for n in nodes]
                                    )
        result = _join(AND, conjuncts)
        if len(self.disjuncts) > 0:
            assert len(self.disjuncts) >= 2
            or_ = _join(OR, [n.to_ce() for n in self.disjuncts])
            if result is None:
                result = or_
            else:
                result = (AND, result, or_)
        if result is not None:
            return result
        else:
            return TOP

    def add_conjunct(self, c: int):
        self.conjuncts.add(c)

    def add_disjunct(self, c: "Node"):
        self.disjuncts.append(c)

    def add_universal(self, r: int, n: "Node"):
        if r in self.existential:
            for other in self.existential[r]:
                # other.merge_with(n)
                other.link(n)
        self.universal[r].append(n)

    def add_existential(self, r: int, n: "Node"):
        if r in self.universal:
            for other in self.universal[r]:
                # n.merge_with(other)
                n.link(other)
        self.existential[r].append(n)

    def link(self, other: "Node") -> None:
        self.linked.append(other)
        for r, unodes in other.universal.items():
            for enode in self.existential[r]:
                for n in unodes:
                    enode.link(n)

    def merge_with(self, other: "Node") -> None:
        """
        Modifies self so it contains all the entries of other
        """
        print("M", self.debug(), "<-", other.debug())
        for c in other.conjuncts:
            self.add_conjunct(c)
        for d in other.disjuncts:
            self.add_disjunct(copy.deepcopy(d))
        for r, nodes in other.existential.items():
            for n in nodes:
                self.add_existential(r, copy.deepcopy(n))
        for r, nodes in other.universal.items():
            for n in nodes:
                self.add_universal(r, copy.deepcopy(n))

    def debug(self) -> str:
        return to_pretty(self.to_ce())

    @property
    def all_conjuncts(self) -> set[int]:
        return self.conjuncts | self.linked_conjuncts

    @property
    def linked_conjuncts(self) -> set[int]:
        if len(self.linked) > 0:
            return set.union(*[node.all_conjuncts for node in self.linked])
        else:
            return set()

    @property
    def all_disjuncts(self) -> list["Node"]:
        return list(itertools.chain(self.disjuncts, *[node.all_disjuncts for node in self.linked]))

    @property
    def all_existential(self) -> dict[int, list["Node"]]:
        result = defaultdict(list)
        result.update(self.existential)
        for node in self.linked:
            for r, nodes in node.all_existential.items():
                result[r].extend(nodes)
        return result

    @property
    def all_universal(self) -> dict[int, list["Node"]]:
        result = defaultdict(list)
        result.update(self.universal)
        for node in self.linked:
            for r, nodes in node.all_universal.items():
                result[r].extend(nodes)
        return result

    def models(self) -> list[Model]:
        atoms = list(self.all_conjuncts)
        disjuncts = self.all_disjuncts
        if len(disjuncts) > 0:
            prod = [[atoms + m for d in self.all_disjuncts for m in d.models()]]
        else:
            prod = [[atoms]]
        existential = self.all_existential.items()
        if len(existential) > 0:
            for r, nodes in existential:
                for n in nodes:
                    prod.append([[(r, m)] for m in n.models()])
        return [list(itertools.chain(*p)) for p in itertools.product(*prod)]

    def leafs(self, shared: set | None = None, linked: set | None = None) -> tuple[
        int, list[tuple[set[int], set[int], set[int]]]]:
        # TODO what about different depths? Only the deepest should be propagated I think?
        disjuncts = self.all_disjuncts
        if len(disjuncts) > 0:
            assert shared is None
            assert linked is None
            shared = self.conjuncts
            linked = self.linked_conjuncts
            return OR, [d.leafs(shared, linked) for d in disjuncts]
        existential = self.all_existential.items()
        if len(existential) > 0:
            result = []
            for r, nodes in existential:
                for n in nodes:
                    result.append(n.leafs())
            return AND, result
        ac = self.linked_conjuncts
        if linked is not None:
            ac |= linked
        return None, (self.conjuncts, shared, linked)

    def apply_mapping(self, mapping: dict[int, int]) -> None:
        self.conjuncts = {(-1 if c < 0 else 1) * mapping[abs(c)] if abs(c) in mapping else c for c in self.conjuncts}
        for n in itertools.chain(self.disjuncts, *self.existential.values(), *self.universal.values()):
            n.apply_mapping(mapping)

    def symbols(self) -> list[set[int]]:
        result = [{abs(s) for s in self.all_conjuncts}]
        for e in itertools.chain(*self.existential.values()):
            result += e.symbols()
        for e in itertools.chain(*self.universal.values()):
            # Ignore the top-level in universals as it is handled elsewhere.
            # TODO Does this work correctly in the case of nested universals?
            result += e.symbols()[1:]
        for d in self.all_disjuncts:
            dsymbols = d.symbols()
            result[0] |= dsymbols[0]
            result += dsymbols[1:]
        return result


class Guide:
    def n_conjuncts(self, depth: int, universal: bool) -> int:
        ...

    def n_disjuncts(self, depth: int, universal: bool) -> int:
        ...

    def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[int]:
        ...

    def universal_roles(self, depth: int, roles: Collection[int], universal: bool) -> list[int]:
        ...


class RandomGuide(Guide):
    def __init__(self, rng: np.random.Generator):
        self.rng = rng

    def n_conjuncts(self, depth: int, universal: bool) -> int:
        return int(self.rng.integers(1, 3))

    def n_disjuncts(self, depth: int, universal: bool) -> int:
        if universal:
            return 0
        else:
            return 2

    def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[int]:
        return [1] * int(self.rng.integers(0, 4))

    def universal_roles(self, depth: int, roles: dict[int, int], universal: bool) -> list[int]:
        candidates = [r for r, v in roles.items() if v >= 2]
        return candidates


class Generator:
    def __init__(self):
        self._classes = 0
        self._roles = 0

    def _new_class(self) -> int:
        self._classes += 1
        return self._classes

    def _new_role(self) -> int:
        self._roles += 1
        return self._roles

    def generate(self, depth: int, guide: Guide, universal: bool = False, disjunct: bool = False) -> Node:
        # TODO not every branch must be the same depth
        node = Node()
        for _ in range(guide.n_conjuncts(depth, universal)):
            node.add_conjunct(self._new_class())
        if depth > 0:
            for r in guide.existential_roles(depth, self._roles, universal):
                while r > self._roles:
                    self._new_role()
                child = self.generate(depth - 1, guide)
                node.add_existential(r, child)
            for r in guide.universal_roles(depth, {r: len(n) for r, n in node.existential.items()}, universal):
                while r > self._roles:
                    self._new_role()
                child = self.generate(depth - 1, guide, universal=True)
                node.add_universal(r, child)
        if not disjunct:
            for _ in range(guide.n_disjuncts(depth, universal)):
                child = self.generate(depth, guide, disjunct=True)
                node.add_disjunct(child)
        return node


def find_relevant_submodels(classes_: int, model: Model) -> list[Model]:
    result = []
    for item in model:
        if item in classes_:
            result.append(model)
        elif isinstance(item, tuple):
            assert len(item) == 2
            result += find_relevant_submodels(classes_, item[1])
    return result


def closing_mapping(leafs) -> dict[int, CE]:
    mapping = {}
    used = Counter()

    def helper(leafs):
        assert isinstance(leafs, tuple)
        assert len(leafs) == 2
        if leafs[0] == OR:
            # Close all - since the leafs are disjunctive, it suffices that any path is satisfiable for the formula to be satisfiable
            for leaf in leafs[1]:
                helper(leaf)
        elif leafs[0] == AND:
            # Close any - since the leafs are conjunctive, it is sufficient for a single leaf to be unsatisfiable for the whole formula to be unsatisfiable
            # TODO perhaps some form of optimization?
            helper(leafs[1][0])
        else:
            assert leafs[0] is None
            leaf, shared, linked = leafs[1]
            if any(atom in mapping for atom in leaf):
                return
            atom = next(iter(leaf))
            best = None
            for l in itertools.chain(linked, shared):
                if best is None or used[best] > used[l]:
                    best = l
                    if used[best] == 0:
                        break
            assert best is not None
            used[best] += 1
            mapping[atom] = -best

    helper(leafs)
    return mapping


def minimizing_mapping(symbols: list[set[int]]) -> dict[int, int]:
    ctr = Counter()
    for symbol in itertools.chain(*symbols):
        ctr[symbol] += 1
    non_unique = {s for s, v in ctr.items() if v > 1}
    unique = set()
    for batch in symbols:
        candidates = {s for s in batch if s not in non_unique}
        assert len(candidates) >= 1, batch
        c = next(iter(candidates))
        assert c not in unique
        unique.add(c)
    cooccurrences = defaultdict(set)
    for batch in symbols:
        for s in batch:
            cooccurrences[s] |= batch
    mapping = {}
    for s, other in cooccurrences.items():
        if s in unique:
            continue
        mapped = {mapping[r] for r in other if r in mapping}
        n = 1
        while n in mapped or n in unique:
            n += 1
        mapping[s] = n
    return mapping


def generate(depth: int, guide: Guide, close: bool, minimize: bool, ce: bool = True) -> CE | Node:
    n = Generator().generate(depth, guide)
    if close:
        n.apply_mapping(closing_mapping(n.leafs()))
    if minimize:
        n.apply_mapping(minimizing_mapping(n.symbols()))
    if ce:
        return n.to_ce()
    else:
        return n


# TODO verify that it works as intended
# TODO optimize

def main():
    for depth in range(1, 10):
        for i in range(100):
            print(depth, i)
            guide = RandomGuide(np.random.default_rng(0xfeed * i + 0xbad * depth))
            generate(depth, guide, True, True)
    # guide = RandomGuide(np.random.default_rng(0xfeed))
    # n = Generator().generate(2, guide)
    # print(n.debug())
    # print("========")
    # leafs = n.leafs()
    # print(*leafs, sep='\n')
    # mapping = closing_mapping(leafs)
    # print(mapping)
    # n.apply_mapping(mapping)
    # print(n.debug())
    # print("========")
    # symbols = n.symbols()
    # print(symbols)
    # print("========")
    # mapping = minimizing_mapping(symbols)
    # print(mapping)
    # n.apply_mapping(mapping)
    # print(*n.leafs(), sep='\n')
    # print("========")
    # ce = n.to_ce()
    # print(to_pretty(ce))
    # with open("/tmp/a.owl", "wt") as f:
    #     to_manchester(ce, "http://example.com/foo", f)


if __name__ == "__main__":
    main()
