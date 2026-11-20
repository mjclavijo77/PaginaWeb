from pathlib import Path
from backend.repositories.base import IReadableRepository, IWritableRepository
from backend.repositories.user_repo import UserRepository
from backend.repositories.favoritos_repo import FavoritosRepository
from backend.repositories.biblioteca_repo import BibliotecaRepository

BASE_DIR = Path(__file__).resolve().parents[2]

ARCHIVO_USUARIOS = BASE_DIR / "usuarios.json"
ARCHIVO_FAVORITOS = BASE_DIR / "favoritos.json"
ARCHIVO_BIBLIOTECA = BASE_DIR / "biblioteca.json"

__all__ = [
    "IReadableRepository",
    "IWritableRepository",
    "UserRepository",
    "FavoritosRepository",
    "BibliotecaRepository",
    "ARCHIVO_USUARIOS",
    "ARCHIVO_FAVORITOS",
    "ARCHIVO_BIBLIOTECA",
]