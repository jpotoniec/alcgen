from collections import defaultdict
from typing import Collection, Generator

import cython
from cython import uint
from cython.operator cimport dereference as deref, preincrement as inc
from libcpp cimport bool as cppbool
from libcpp.unordered_map cimport unordered_map
from libcpp.unordered_set cimport unordered_set
from libcpp.vector cimport vector

cdef class Cooccurrences:
    cdef unordered_map[uint, uint] _parent
    cdef unordered_map[uint, uint] _rank

    cpdef cython.uint find(self, x: uint):
        # if x not in self._parent:
        if not self._parent.contains(x):
            self._parent[x] = x
            self._rank[x] = 0
            return x
        p: uint = self._parent[x]
        if p != x:
            p = self.find(p)
            self._parent[x] = p
            return p
        else:
            return x

    cpdef void union(self, x: uint, y: uint):
        x = self.find(x)
        y = self.find(y)
        if x == y:
            return
        if self._rank[x] < self._rank[y]:
            x, y = y, x
        self._parent[y] = x
        if self._rank[x] == self._rank[y]:
            self._rank[x] += 1

    cpdef void union_many(self, items: unordered_set[uint]):
        if items.empty():
            return
        i = items.cbegin()
        y = self.find(deref(i))
        while inc(i) != items.cend():
            x = self.find(deref(i))
            if x == y:
                continue
            if self._rank[x] < self._rank[y]:
                x, y = y, x
            self._parent[y] = x
            if self._rank[x] == self._rank[y]:
                self._rank[x] += 1
            y = x

    def items(self) -> Generator[tuple[int, int], None, None]:
        for x in self._parent:
            yield x.first, self.find(x.first)

    # TODO cythonize better
    def to_list(self) -> list[set]:
        result = defaultdict(set)
        for x in self._parent:
            x = x[0]
            p = self.find(x)
            result[p].add(x)
        return list(result.values())

    # TODO cythonize better
    def to_dict(self) -> dict:
        result = {}
        for part in self.to_list():
            for x in part:
                result[x] = part
        return result

    cpdef cppbool has_nonempty_intersection(self, xs: vector[uint], ys: vector[uint]):
        cdef unordered_set[uint] ys_parents
        cdef unordered_map[uint, uint].const_iterator p
        cdef unordered_map[uint, uint].const_iterator end = self._parent.cend()
        for y in ys:
            p = self._parent.find(y)
            if p != end:
                ys_parents.insert(deref(p).second)
        for x in xs:
            p = self._parent.find(x)
            if p != end and ys_parents.contains(deref(p).second):
                return True
        return False

    add = union_many

    @property
    def max_item(self):
        cdef cython.uint m = 0
        cdef cython.uint v
        for p in self._parent:
            v = p.first
            if v > m:
                m = v
        return m
