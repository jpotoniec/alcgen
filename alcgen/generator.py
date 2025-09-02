import itertools
import typing
from collections import defaultdict, Counter

from alcgen.cooccurrences import Cooccurrences
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


def nonclosing_mapping(cooccurrences: Cooccurrences) -> dict[int, int]:
    n_symbols = cooccurrences.max_item + 1
    mapping = [None] * n_symbols
    used = [False] * n_symbols
    while True:
        families = cooccurrences.to_list()
        if len(families) <= 1:
            break
        pair = []
        for f in families:
            for s in f:
                if used[s]:
                    continue
                pair.append(s)
                break
            if len(pair) == 2:
                break
        if len(pair) < 2:
            break
        assert len(pair) == 2
        mapping[pair[0]] = -pair[1]
        used[pair[0]] = True
        used[pair[1]] = True
        cooccurrences.union_many(pair)
    return {k: v for k, v in enumerate(mapping) if v is not None}


def minimizing_mapping(cooccurrences: Cooccurrences) -> dict[int, int]:
    max_symbol = cooccurrences.max_item
    mapping = [None] * (max_symbol + 1)
    last = Counter()
    for x, p in cooccurrences.items():
        last[p] += 1
        mapping[x] = last[p]
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


def merge_constraint_into_symbols(cooccurrences: Cooccurrences, constraint: tuple[set[int], set[int]]) -> None:
    """
    For the constraint to be satisfied the left set must differ from the right set, i.e., they must differ by at least one element.
    """
    left, right = constraint
    left = {abs(x) for x in left}
    right = {abs(y) for y in right}
    if cooccurrences.has_nonempty_intersection(left, right):
        # Already satisfied
        return
    any_left = next(iter(left))
    any_right = next(iter(right))
    cooccurrences.add({any_left, any_right})


def build_index(symbols: list[set[int]]) -> defaultdict[int, set[int]]:
    result = defaultdict(set[int])
    for i, part in enumerate(symbols):
        for s in part:
            result[s].add(i)
    return result


def do_close(n: Node):
    n.apply_mapping(closing_mapping(n.leafs()))


def do_minimize(n: Node, cooccurrences: Cooccurrences | None = None):
    if cooccurrences is None:
        cooccurrences = n.cooccurrences()
        for constraint in compute_constraints(n):
            merge_constraint_into_symbols(cooccurrences, constraint)
    n.apply_mapping(minimizing_mapping(cooccurrences))


def introduce_negations(n: Node):
    cooccurrences = n.cooccurrences()
    for constraint in compute_constraints(n):
        merge_constraint_into_symbols(cooccurrences, constraint)
    n.apply_mapping(nonclosing_mapping(cooccurrences))
    return cooccurrences


def generate(depth: int, guide: Guide, close: bool, minimize: bool, ce: bool = True) -> CE | Node:
    n = Generator().generate(depth, guide)
    cooccurrences = None
    if close:
        do_close(n)
    else:
        cooccurrences = introduce_negations(n)
    if minimize:
        do_minimize(n, cooccurrences)
    if ce:
        return n.to_ce()
    else:
        return n
