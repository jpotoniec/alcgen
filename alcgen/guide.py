from typing import Sequence, TypeVar

_T = TypeVar('_T')


class Guide:
    def _select(self, items: list[_T]) -> _T:
        raise NotImplementedError()

    def rule(self, n_rules: int) -> Sequence[int]:
        raise NotImplementedError()

    def steps(self) -> int:
        raise NotImplementedError()

    def select_class(self, classes: list[int]) -> int:
        return self._select(classes)

    def select_role(self, roles: list[int]) -> int:
        return self._select(roles)

    def select_class_role_pair(self, ar: list[tuple[int, int]]):
        return self._select(ar)
