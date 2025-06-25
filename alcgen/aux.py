from typing import TypeVar

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
