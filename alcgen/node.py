import itertools
from collections import defaultdict

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
        return None, (self.conjuncts, shared or set(), linked or set())

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

    def depth(self) -> int:
        d = 0
        for e in itertools.chain(*self.existential.values()):
            d = max(d, e.depth() + 1)
        for e in itertools.chain(*self.universal.values()):
            d = max(d, e.depth() + 1)
        return d
