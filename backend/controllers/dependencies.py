from pathlib import Path
from fastapi import Request
from fastapi.templating import Jinja2Templates

from backend.game_facade import GameCatalogFacade
from backend.repositories import (
    ARCHIVO_BIBLIOTECA,
    ARCHIVO_FAVORITOS,
    ARCHIVO_USUARIOS,
    BibliotecaRepository,
    FavoritosRepository,
    UserRepository,
)

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_user_repo() -> UserRepository:
    return UserRepository(ARCHIVO_USUARIOS)


def get_favoritos_repo() -> FavoritosRepository:
    return FavoritosRepository(ARCHIVO_FAVORITOS)


def get_biblioteca_repo() -> BibliotecaRepository:
    return BibliotecaRepository(ARCHIVO_BIBLIOTECA)


def get_catalogo_facade() -> GameCatalogFacade:
    return GameCatalogFacade()


def obtener_correo_sesion(request: Request) -> str | None:
    return request.session.get("correo")


def obtener_usuario_sesion(request: Request) -> str | None:
    return request.session.get("usuario")


def agregar_flash(request: Request, mensaje: str) -> None:
    mensajes = request.session.get("_flashes", [])
    mensajes.append(mensaje)
    request.session["_flashes"] = mensajes


def obtener_flashes(request: Request) -> list[str]:
    return request.session.pop("_flashes", [])