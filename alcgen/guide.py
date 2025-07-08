from typing import Collection


class Guide:
    def n_conjuncts(self, depth: int, universal: bool) -> int:
        ...

    def n_disjuncts(self, depth: int, universal: bool) -> int:
        ...

    def existential_roles(self, depth: int, n_roles: int, universal: bool) -> list[int]:
        ...

    def universal_roles(self, depth: int, roles: Collection[int], universal: bool) -> list[int]:
        ...
