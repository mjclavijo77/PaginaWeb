from pathlib import Path

from backend.models.schemas import (
    BibliotecaEstadoPatch,
    BibliotecaItemCreate,
    BibliotecaItemDB,
    BibliotecaItemUpdate,
)
from backend.repositories.base import IReadableRepository, IWritableRepository
from backend.repositories.json_storage import JsonFileStorage


class BibliotecaRepository(IReadableRepository[dict], IWritableRepository[dict]):
    """Gestiona la biblioteca personal de videojuegos con estados y notas."""

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
            item
            for item in self.listar_todos()
            if str(item.get("correo", "")).strip().lower() == correo_norm
        ]

    def obtener_por_id(self, correo: str, juego_id: int) -> dict | None:
        correo_norm = correo.strip().lower()
        for item in self.listar_todos():
            if (
                str(item.get("correo", "")).strip().lower() == correo_norm
                and int(item.get("juego_id", -1)) == int(juego_id)
            ):
                return item
        return None

    def agregar(self, correo: str, datos: BibliotecaItemCreate) -> dict | None:
        correo_norm = correo.strip().lower()
        if not correo_norm or self.obtener_por_id(correo_norm, datos.juego_id):
            return None

        items = self.listar_todos()
        nuevo = BibliotecaItemDB(
            correo=correo_norm,
            juego_id=datos.juego_id,
            nombre=datos.nombre.strip(),
            estado=datos.estado,
            calificacion_personal=datos.calificacion_personal,
            notas=datos.notas.strip(),
            juego=datos.juego,
        ).model_dump()

        items.append(nuevo)
        self.guardar_todos(items)
        return nuevo

    def reemplazar(self, correo: str, juego_id: int, datos: BibliotecaItemUpdate) -> dict | None:
        """Soporta PUT: reemplaza estado, calificación y notas de un juego existente."""
        correo_norm = correo.strip().lower()
        items = self.listar_todos()
        actualizado = None

        for item in items:
            if (
                str(item.get("correo", "")).strip().lower() == correo_norm
                and int(item.get("juego_id", -1)) == int(juego_id)
            ):
                item["estado"] = datos.estado
                item["calificacion_personal"] = datos.calificacion_personal
                item["notas"] = datos.notas.strip()
                actualizado = item
                break

        if actualizado is not None:
            self.guardar_todos(items)
        return actualizado

    def actualizar_parcial(self, correo: str, juego_id: int, datos: BibliotecaEstadoPatch) -> dict | None:
        """Soporta PATCH: modifica únicamente los campos enviados."""
        correo_norm = correo.strip().lower()
        items = self.listar_todos()
        actualizado = None

        for item in items:
            if (
                str(item.get("correo", "")).strip().lower() == correo_norm
                and int(item.get("juego_id", -1)) == int(juego_id)
            ):
                if datos.estado is not None:
                    item["estado"] = datos.estado
                if datos.calificacion_personal is not None:
                    item["calificacion_personal"] = datos.calificacion_personal
                if datos.notas is not None:
                    item["notas"] = datos.notas.strip()
                actualizado = item
                break

        if actualizado is not None:
            self.guardar_todos(items)
        return actualizado

    def eliminar(self, correo: str, juego_id: int) -> bool:
        correo_norm = correo.strip().lower()
        items = self.listar_todos()

        restantes = [
            item
            for item in items
            if not (
                str(item.get("correo", "")).strip().lower() == correo_norm
                and int(item.get("juego_id", -1)) == int(juego_id)
            )
        ]

        if len(restantes) == len(items):
            return False

        self.guardar_todos(restantes)
        return True