import itertools
from collections import defaultdict, Counter

from .guide import Guide
from .node import Node
from .syntax import CE, AND, OR


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
