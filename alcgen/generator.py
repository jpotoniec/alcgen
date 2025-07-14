import itertools
import typing
from collections import defaultdict, Counter

from alcgen.guide import Guide
from alcgen.leaf import Leafs, Leaf
from alcgen.node import Node
from alcgen.syntax import CE, AND, OR


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
        node = Node()
        for _ in range(guide.n_conjuncts(depth, universal)):
            node.add_conjunct(self._new_class())
        if depth > 0:
            for r, d in guide.existential_roles(depth, self._roles, universal):
                while r > self._roles:
                    self._new_role()
                child = self.generate(d, guide)
                node.add_existential(r, child)
            for r, d in guide.universal_roles(depth,
                                              {r: [n.depth() for n in nodes] for r, nodes in node.existential.items()},
                                              universal):
                while r > self._roles:
                    self._new_role()
                child = self.generate(d, guide, universal=True)
                node.add_universal(r, child)
        if not disjunct:
            for _ in range(guide.n_disjuncts(depth, universal)):
                child = self.generate(depth, guide, disjunct=True)
                node.add_disjunct(child)
        return node


def closing_mapping(leafs) -> dict[int, CE]:
    mapping = {}
    used = Counter()

    def helper(leafs: Leafs):
        if leafs.op == OR:
            # Close all - since the leafs are disjunctive, it suffices that any path is satisfiable for the formula to be satisfiable
            for leaf in leafs.leafs:
                if not helper(leaf):
                    return False
            return True
        elif leafs.op == AND:
            # Close any - since the leafs are conjunctive, it is sufficient for a single leaf to be unsatisfiable for the whole formula to be unsatisfiable
            # We prefer the deepest, but that is a heuristic with no guarantees
            max_depth = max([l.depth for l in leafs.leafs])
            for leaf in leafs.leafs:
                if leaf.depth == max_depth and helper(leaf):
                    return True
            else:
                return False
        else:
            assert leafs.op is None
            assert isinstance(leafs.leafs, Leaf)
            atoms = leafs.leafs.atoms
            shared = leafs.leafs.shared
            linked = leafs.leafs.linked
            if any(atom in mapping for atom in atoms):
                return True
            atom = next(iter(atoms))
            best = None
            for l in itertools.chain(linked, shared):
                if best is None or used[best] > used[l]:
                    best = l
                    if used[best] == 0:
                        break
            if best is None:
                for l in atoms - {atom}:
                    if best is None or used[best] > used[l]:
                        best = l
                        if used[best] == 0:
                            break
            if best is not None:
                used[best] += 1
                mapping[atom] = -best
                return True
            else:
                return False

    status = helper(leafs)
    if not status:
        raise Exception("Cannot fully close the formula")
    return mapping


def minimizing_mapping(symbols: list[set[int]]) -> dict[int, int]:
    cooccurrences = defaultdict(set)
    for batch in symbols:
        for s in batch:
            cooccurrences[s] |= batch
    max_symbol = max(cooccurrences.keys())
    mapping = [None] * (max_symbol + 1)
    for s, other in cooccurrences.items():
        mapped = {mapping[r] for r in other if mapping[r] is not None}
        n = 1
        while n in mapped:
            n += 1
        mapping[s] = n
    return {i: v for i, v in enumerate(mapping) if v is not None}


def nonequivalence_constraints(a: Node, b: Node, lazy: bool) -> list[tuple[set[int], set[int]]]:
    def count_signs(items: set[int]) -> tuple[int, int]:
        p, n = 0, 0
        for i in items:
            if i > 0:
                p += 1
            else:
                assert i < 0
                n += 1
        return p, n

    if len(a.conjuncts) != len(b.conjuncts):
        return []
    if count_signs(a.conjuncts) != count_signs(b.conjuncts):
        return []
    if a.descriptor != b.descriptor:
        return []
    if not lazy:
        """
        We return the first, non-empty set of constraints:
        1. to ensure universal restrictions are different
        2. to ensure existential restrictions are different
        3. to ensure conjuncts at the current level are different
        We prefer to differentiate in constraints rather than top-level and in universal rather than in existential restrictions.
        This is a heuristic to limit the number of constraints.
        """
        for acoll, bcoll in [(a.universal, b.universal), (a.existential, b.existential)]:
            result = []
            for r, anodes in acoll.items():
                bnodes = bcoll[r]
                if len(anodes) != len(bnodes):
                    return []
                hits = [False] * len(bnodes)
                hit = True
                for i, x in enumerate(anodes):
                    for j, y in enumerate(bnodes):
                        if y is None:
                            continue
                        req = nonequivalence_constraints(x, y, lazy)
                        if len(req) > 0:
                            result.extend(req)
                            hits[j] = True
                            hit = True
                    if not hit:
                        return []
                if not all(hits):
                    return []
            if len(result) > 0:
                return result
    # If lazy - we produce a constraint as soon as possible, without going down - it is perhaps less interesting, but more efficient
    return [(a.conjuncts, b.conjuncts)]


def compute_constraints(n: Node, lazy: bool = True) -> typing.Generator[tuple[set[int], set[int]], None, None]:
    for nodes in itertools.chain(n.existential.values(), n.universal.values()):
        for i, x in enumerate(nodes):
            for y in nodes[i + 1:]:
                yield from nonequivalence_constraints(x, y, lazy)
            yield from compute_constraints(x, lazy)


def union(*sets: set[int]) -> set[int]:
    result = set()
    result.update(*sets)
    return result


def merge_constraint_into_symbols(symbols: list[set[int]], index: defaultdict[int, set[int]],
                                  constraint: tuple[set[int], set[int]]) -> None:
    """
    For the constraint to be satisfied the left set must differ from the right set, i.e., they must differ by at least one element.
    """
    left, right = constraint
    left = {abs(x) for x in left}
    right = {abs(y) for y in right}
    lidx = union(*[index[s] for s in left])
    ridx = union(*[index[s] for s in right])

    if len(lidx & ridx) > 0:
        # Already satisfied
        return
    lidx |= ridx
    if len(lidx) > 0:
        i = next(iter(lidx))
    else:
        i = 0
    if len(left & symbols[i]) == 0:
        s = next(iter(left))
        symbols[i].add(s)
        index[s].add(i)
    if len(right & symbols[i]) == 0:
        s = next(iter(right))
        symbols[i].add(s)
        index[s].add(i)


def build_index(symbols: list[set[int]]) -> defaultdict[int, set[int]]:
    result = defaultdict(set[int])
    for i, part in enumerate(symbols):
        for s in part:
            result[s].add(i)
    return result


def do_close(n: Node):
    n.apply_mapping(closing_mapping(n.leafs()))


def do_minimize(n: Node):
    symbols = n.symbols()
    index = build_index(symbols)
    for constraint in compute_constraints(n):
        merge_constraint_into_symbols(symbols, index, constraint)
    n.apply_mapping(minimizing_mapping(symbols))


def generate(depth: int, guide: Guide, close: bool, minimize: bool, ce: bool = True) -> CE | Node:
    n = Generator().generate(depth, guide)
    if close:
        do_close(n)
    if minimize:
        do_minimize(n)
    if ce:
        return n.to_ce()
    else:
        return n
