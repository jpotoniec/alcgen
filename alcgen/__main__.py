import fire
import numpy as np

from alcgen.generator import generate
from alcgen.guide import Guide
from alcgen.random_guide import RandomGuide
from alcgen.syntax import to_pretty


class BaselineGuide(Guide):
    def n_conjuncts(self, depth: int, universal: bool) -> int:
        return 2

    def n_disjuncts(self, depth: int, universal: bool) -> int:
        if universal:
            return 0
        else:
            return 2

    def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
        return [(1, depth - 1), (1, depth - 1)]

    def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
        return [(1, depth - 1)]

def main():
    class MyGuide(BaselineGuide):
        def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[tuple[int, int]]:
            return [(1, depth - 1)] * 5

        def universal_roles(self, depth: int, roles: dict[int, list[int]], universal: bool) -> list[tuple[int, int]]:
            return []

    ce = generate(5, MyGuide(), True, True)
    assert ce is not None
    return

    for depth in range(5, 6):
        for i in range(1):
            print(depth, i)
            guide = RandomGuide(np.random.default_rng(0xfeed * i + 0xbad * depth))
            ce = generate(depth, guide, True, True)
            print(to_pretty(ce))
    # guide = RandomGuide(np.random.default_rng(0xfeed))
    # n = Generator().generate(2, guide)
    # print(n.debug())
    # print("========")
    # leafs = n.leafs()
    # print(*leafs, sep='\n')
    # mapping = closing_mapping(leafs)
    # print(mapping)
    # n.apply_mapping(mapping)
    # print(n.debug())
    # print("========")
    # symbols = n.symbols()
    # print(symbols)
    # print("========")
    # mapping = minimizing_mapping(symbols)
    # print(mapping)
    # n.apply_mapping(mapping)
    # print(*n.leafs(), sep='\n')
    # print("========")
    # ce = n.to_ce()
    # print(to_pretty(ce))
    # with open("/tmp/a.owl", "wt") as f:
    #     to_manchester(ce, "http://example.com/foo", f)


if __name__ == "__main__":
    fire.Fire(main)
