# distutils: language=c++
# distutils: extra_compile_args=["-std=c++20"]
from cython import uint
from cython.cimports.libcpp import bool as cppbool
from cython.cimports.libcpp.pair import pair
from cython.cimports.libcpp.set import set as cppset
from cython.cimports.libcpp.unordered_map import unordered_map
from cython.cimports.libcpp.vector import vector
from cython.operator import dereference as deref, preincrement as inc

cpdef unordered_map[uint, cppset[uint]] build_index(symbols: vector[cppset[uint]]):
    result: unordered_map[uint, cppset[uint]]
    i: uint
    n: uint
    n = symbols.size()
    s: uint
    for i in range(n):
        for s in symbols[i]:
            result[s].insert(i)
    return result

cpdef unordered_map[uint, uint] minimizing_mapping(vector[cppset[uint]]& symbols,
                                                   vector[pair[cppset[uint], cppset[uint]]]& constraints):
    merge_constraints_into_symbols(symbols, constraints)
    cooccurrences: unordered_map[uint, cppset[uint]]
    max_symbol: uint = 0
    batch: cppset[uint]
    s: uint
    o: uint
    for batch in symbols:
        for s in batch:
            # t: cppset[uint] =
            cooccurrences[s].insert(batch.cbegin(), batch.cend())
            max_symbol = max(max_symbol, s)
    mapping: vector[uint]
    mapping.reserve(max_symbol + 1)
    p: pair[uint, cppset[uint]]
    for p in cooccurrences:
        s: uint = p.first
        other: cppset[uint] = p.second
        r: uint
        mapped: cppset[uint]
        for r in other:
            if mapping[r] > 0:
                mapped.insert(r)
        n: uint = 1
        while mapped.contains(n):
            n += 1
        mapping[s] = n
    result: unordered_map[uint, uint]
    i: uint
    for i in range(max_symbol + 1):
        v = mapping[i]
        if v > 0:
            result[i] = v
    return result
#
# cdef cppset[uint] union(sets: vector[cppset[uint]]):
#     # TODO see std::set_union
#     result: cppset[uint]
#     item: cppset[uint]
#     for item in sets:
#         result.insert(item.cbegin(), item.cend())
#     return result

# careful, they must be sorted
cdef cppbool has_nonempty_intersection(cppset[uint]& set1, cppset[uint]& set2):
    i = set1.cbegin()
    j = set2.cbegin()
    while i != set1.cend() and j != set2.cend():
        if deref(i) < deref(j):
            inc(i)
        elif deref(i) > deref(j):
            inc(j)
        else:
            return True
    return False

cdef merge_constraint_into_symbols(vector[cppset[uint]]& symbols,
                                   unordered_map[uint, cppset[uint]]& index,
                                   pair[cppset[uint], cppset[uint]]& constraint):
    """
    For the constraint to be satisfied the left set must differ from the right set, i.e., they must differ by at least one element.
    """
    left: cppset[uint]
    x: uint
    for x in constraint.first:
        left.insert(abs(x))
    right: cppset[uint]
    for x in constraint.second:
        right.insert(abs(x))
    lidx: cppset[uint]
    for x in left:
        lidx.insert(index[x].cbegin(), index[x].cend())
    ridx: cppset[uint]
    for x in right:
        ridx.insert(index[x].cbegin(), index[x].cend())

    if has_nonempty_intersection(lidx, ridx):
        # Already satisfied
        return
    lidx.insert(ridx.cbegin(), ridx.cend())
    if lidx.size() > 0:
        i = deref(lidx.begin())
    else:
        i = 0
    if not has_nonempty_intersection(left, symbols[i]):
        s = deref(left.cbegin())
        symbols[i].insert(s)
        index[s].insert(i)
    if not has_nonempty_intersection(right, symbols[i]):
        s = deref(right.cbegin())
        symbols[i].insert(s)
        index[s].insert(i)

cdef merge_constraints_into_symbols(vector[cppset[uint]]& symbols,
                                    vector[pair[cppset[uint], cppset[uint]]]& constraints):
    index = build_index(symbols)
    for constraint in constraints:
        merge_constraint_into_symbols(symbols, index, constraint)

cpdef vector[cppset[uint]] merge_constraints_into_symbols_for_test(vector[cppset[uint]]& symbols,
                                                                   vector[pair[cppset[uint], cppset[uint]]
                                                                          ]& constraints):
    merge_constraints_into_symbols(symbols, constraints)
    return symbols
