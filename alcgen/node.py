import itertools
from collections import defaultdict

from alcgen.cooccurrences import Cooccurrences
from alcgen.leaf import Leafs, Leaf
from alcgen.syntax import CE, AND, ANY, OR, TOP, to_pretty, ALL, NOT


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
        # TODO Invalidate the descriptor if a new operand is added
        self._descriptor = None
        for arg in args:
            if isinstance(arg, Node):
                self.disjuncts.append(arg)
            elif isinstance(arg, tuple):
                assert len(arg) == 2
                self.add_existential(*arg)
            else:
                self.add_conjunct(arg)

    def to_ce(self) -> CE:
        def _add(left, op, right):
            if left is None:
                return right
            else:
                return op, left, right

        result = None
        for i in self.conjuncts:
            result = _add(result, AND, (NOT, -i) if i < 0 else i)
        for r, nodes in self.existential.items():
            for n in nodes:
                result = _add(result, AND, (ANY, r, n.to_ce()))
        for r, nodes in self.universal.items():
            for n in nodes:
                result = _add(result, AND, (ALL, r, n.to_ce()))

        if len(self.disjuncts) > 0:
            assert len(self.disjuncts) >= 2
            or_ = None
            for n in self.disjuncts:
                or_ = _add(or_, OR, n.to_ce())
            if or_ is not None:
                result = _add(result, AND, or_)
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

    def debug(self) -> str:
        return to_pretty(self.to_ce())

    def gather_all_conjuncts(self, target: set[int]) -> set[int]:
        target.update(self.conjuncts)
        self.gather_linked_conjuncts(target)
        return target

    def gather_linked_conjuncts(self, target: set[int]) -> set[int]:
        for node in self.linked:
            node.gather_all_conjuncts(target)
        return target

    def gather_all_disjuncts(self, target: list["Node"]) -> list["Node"]:
        target += self.disjuncts
        for node in self.linked:
            node.gather_all_disjuncts(target)
        return target

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

    def leafs(self, shared: set | None = None, linked: set | None = None, depth: int = 0) -> Leafs:
        disjuncts = self.gather_all_disjuncts([])
        if len(disjuncts) > 0:
            assert shared is None
            assert linked is None
            shared = self.conjuncts
            linked = self.gather_linked_conjuncts(set())
            # Don't increase depth in disjunction, because that is not another level of the model
            leafs = [d.leafs(shared, linked, depth) for d in disjuncts]
            return Leafs(OR, leafs, max(leaf.depth for leaf in leafs))
        existential = self.all_existential.items()
        if len(existential) > 0:
            leafs = []
            for r, nodes in existential:
                for n in nodes:
                    leafs.append(n.leafs(depth=depth + 1))
            return Leafs(AND, leafs, max(leaf.depth for leaf in leafs))
        ac = self.gather_linked_conjuncts(set())
        if linked is not None:
            ac |= linked
        return Leafs(None, Leaf(self.conjuncts, shared or set(), ac), depth)

    def apply_mapping(self, mapping: dict[int, int]) -> None:
        self.conjuncts = {(-1 if c < 0 else 1) * mapping[abs(c)] if abs(c) in mapping else c for c in self.conjuncts}
        for n in itertools.chain(self.disjuncts, *self.existential.values(), *self.universal.values()):
            n.apply_mapping(mapping)

    def _cooccurrences(self, target: Cooccurrences, prefix: set[int] | None):
        top = {abs(s) for s in self.gather_all_conjuncts(set())}
        if prefix is not None:
            top.update(prefix)
        target.add(top)
        for e in itertools.chain(*self.existential.values()):
            e._cooccurrences(target, None)
        for e in itertools.chain(*self.universal.values()):
            e._cooccurrences(target, None)
        for d in self.gather_all_disjuncts([]):
            d._cooccurrences(target, top)

    def cooccurrences(self) -> Cooccurrences:
        result = Cooccurrences()
        self._cooccurrences(result, None)
        return result

    def depth(self) -> int:
        d = 0
        for e in itertools.chain(*self.existential.values()):
            d = max(d, e.depth() + 1)
        for e in itertools.chain(*self.universal.values()):
            d = max(d, e.depth() + 1)
        return d

    @property
    def descriptor(self):
        if self._descriptor is None:
            c = len(self.conjuncts)
            d = sorted([n.descriptor for n in self.disjuncts])
            e = sorted([(r, n.descriptor) for r, nodes in self.existential.items() for n in nodes])
            u = sorted([(r, n.descriptor) for r, nodes in self.universal.items() for n in nodes])
            self._descriptor = (c, d, e, u)
        return self._descriptor
