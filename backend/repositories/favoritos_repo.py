from pathlib import Path

from backend.repositories.base import IReadableRepository, IWritableRepository
from backend.repositories.json_storage import JsonFileStorage


class FavoritosRepository(IReadableRepository[dict], IWritableRepository[dict]):
    """Gestiona los videojuegos favoritos por usuario."""

    def __init__(self, ruta_archivo: Path):
        self.storage = JsonFileStorage(ruta_archivo)

    def listar_todos(self) -> list[dict]:
        datos = self.storage.leer([])
        return datos if isinstance(datos, list) else []

    def guardar_todos(self, items: list[dict]) -> None:
        self.storage.escribir(items)

    def obtener_por_usuario(self, correo: str) -> list[dict]:
        correo_norm = correo.strip().lower()
        return [
            fav
            for fav in self.listar_todos()
            if str(fav.get("correo", "")).strip().lower() == correo_norm
        ]

    def es_favorito(self, correo: str, nombre: str) -> bool:
        nombre_norm = nombre.strip().casefold()
        return any(
            str(fav.get("nombre", "")).strip().casefold() == nombre_norm
            for fav in self.obtener_por_usuario(correo)
        )

    def agregar(self, correo: str, juego: dict) -> bool:
        if not isinstance(juego, dict):
            return False

        correo_norm = correo.strip().lower()
        nombre = str(juego.get("nombre", "")).strip()
        if not correo_norm or not nombre or self.es_favorito(correo_norm, nombre):
            return False

        favoritos = self.listar_todos()
        favoritos.append({
            "correo": correo_norm,
            "nombre": nombre,
            "juego": juego,
        })
        self.guardar_todos(favoritos)
        return True

    def eliminar(self, correo: str, nombre: str) -> bool:
        correo_norm = correo.strip().lower()
        nombre_norm = nombre.strip().casefold()
        favoritos = self.listar_todos()

        restantes = [
            fav
            for fav in favoritos
            if not (
                str(fav.get("correo", "")).strip().lower() == correo_norm
                and str(fav.get("nombre", "")).strip().casefold() == nombre_norm
            )
        ]

        if len(restantes) == len(favoritos):
            return False

        self.guardar_todos(restantes)
        return True