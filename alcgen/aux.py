from typing import TypeVar, Sequence

T = TypeVar('T')


def insert_maximal(target: list[set[T]], item: set[T]):
    indices = []
    for i, t in enumerate(target):
        if item <= t:
            indices.append(i)
        elif t <= item:
            target[i] = item
            indices.append(i)
    if len(indices) == 0:
        target.append(item)
    elif len(indices) > 1:
        for i in indices[-1:0:-1]:
            del target[i]


def intersection(sets: Sequence[set]) -> set:
    if len(sets) == 0:
        return set()
    if len(sets) == 1:
        return sets[0]
    return set(sets[0]).intersection(*sets[1:])


def has_non_empty_intersection(a: set, b: set) -> bool:
    if len(a) > len(b):
        return has_non_empty_intersection(b, a)
    if len(a) == 0 or len(b) == 0:
        return False
    return any(x in b for x in a)
