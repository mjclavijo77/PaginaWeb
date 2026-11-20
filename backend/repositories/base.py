from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class IReadableRepository(ABC, Generic[T]):
    """Principio I (Segregación de Interfaces): contrato solo de lectura."""

    @abstractmethod
    def listar_todos(self) -> list[T]:
        raise NotImplementedError


class IWritableRepository(ABC, Generic[T]):
    """Principio I (Segregación de Interfaces): contrato de escritura."""

    @abstractmethod
    def guardar_todos(self, items: list[T]) -> None:
        raise NotImplementedError