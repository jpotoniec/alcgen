from collections import defaultdict
from typing import Collection, Generator


class Cooccurrences:
    def __init__(self):
        self._parent = {}
        self._rank = {}

    def find(self, x: int):
        if x not in self._parent:
            self._parent[x] = x
            self._rank[x] = 0
            return x
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, x: int, y: int):
        self.union_many([x, y])

    def union_many(self, items: Collection[int]):
        if len(items) == 0:
            return
        it = iter(items)
        y = self.find(next(it))
        ry = self._rank[y]
        for x in it:
            x = self.find(x)
            if x == y:
                continue
            rx = self._rank[x]
            if rx < ry:
                x, y = y, x
                # don't swap rx and ry, since they would be swapped back anyhow
            elif rx == ry:
                self._rank[x] += 1
                ry = rx + 1
            else:
                ry = rx
            self._parent[y] = x
            y = x

    def items(self) -> Generator[tuple[int, int], None, None]:
        for x in self._parent.keys():
            yield x, self.find(x)

    def to_list(self) -> list[set]:
        result = defaultdict(set)
        for x in self._parent.keys():
            p = self.find(x)
            result[p].add(x)
        return list(result.values())

    def to_dict(self) -> dict:
        result = {}
        for part in self.to_list():
            for x in part:
                result[x] = part
        return result

    def has_nonempty_intersection(self, xs: Collection[int], ys: Collection[int]) -> bool:
        ys = {self._parent.get(y, None) for y in ys} - {None}
        for x in xs:
            x = self._parent.get(x, None)
            if x is None:
                continue
            if x in ys:
                return True
        return False

    add = union_many

    @property
    def max_item(self):
        return max(self._parent.keys())
