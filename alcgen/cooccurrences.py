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
        p = self._parent[x]
        if p != x:
            self._parent[x] = p = self.find(p)
            return p
        else:
            return x

    def union(self, x: int, y: int):
        x = self.find(x)
        y = self.find(y)
        if x == y:
            return
        if self._rank[x] < self._rank[y]:
            x, y = y, x
        self._parent[y] = x
        if self._rank[x] == self._rank[y]:
            self._rank[x] += 1

    def union_many(self, items: Collection[int]):
        if len(items) == 0:
            return
        i = iter(items)
        y = self.find(next(i))
        try:
            while True:
                x = self.find(next(i))
                if x == y:
                    continue
                if self._rank[x] < self._rank[y]:
                    x, y = y, x
                self._parent[y] = x
                if self._rank[x] == self._rank[y]:
                    self._rank[x] += 1
                y = x
        except StopIteration:
            pass

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
