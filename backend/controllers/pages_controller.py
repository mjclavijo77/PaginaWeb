import json
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.controllers.dependencies import (
    agregar_flash,
    get_biblioteca_repo,
    get_catalogo_facade,
    get_favoritos_repo,
    obtener_correo_sesion,
    obtener_flashes,
    obtener_usuario_sesion,
    templates,
)
from backend.game_facade import GameCatalogFacade
from backend.models.schemas import BibliotecaItemCreate
from backend.repositories import BibliotecaRepository, FavoritosRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Páginas (Vistas HTML)"])


@router.get("/", response_class=HTMLResponse, name="inicio")
def inicio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "usuario": obtener_usuario_sesion(request),
            "mensajes": obtener_flashes(request),
        },
    )


@router.get("/resultados", response_class=HTMLResponse, name="resultados")
def resultados(
    request: Request,
    q: str = Query(default=""),
    catalogo: GameCatalogFacade = Depends(get_catalogo_facade),
    fav_repo: FavoritosRepository = Depends(get_favoritos_repo),
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
):
    nombre_juego = q.strip()
    correo = obtener_correo_sesion(request)
    usuario = obtener_usuario_sesion(request)

    if not nombre_juego:
        return templates.TemplateResponse(
            request=request,
            name="resultados.html",
            context={
                "juego": None,
                "error": "Debes escribir el nombre de un videojuego.",
                "usuario": usuario,
                "es_favorito": False,
                "en_biblioteca": False,
                "mensajes": obtener_flashes(request),
            },
        )

    try:
        datos = catalogo.obtener_datos_completos(nombre_juego)
    except Exception:
        logger.exception("Error al consultar las APIs para %s", nombre_juego)
        return templates.TemplateResponse(
            request=request,
            name="resultados.html",
            context={
                "juego": None,
                "error": "Ocurrió un problema al consultar los servicios de videojuegos.",
                "usuario": usuario,
                "es_favorito": False,
                "en_biblioteca": False,
                "mensajes": obtener_flashes(request),
            },
        )

    if not datos:
        return templates.TemplateResponse(
            request=request,
            name="resultados.html",
            context={
                "juego": None,
                "error": "No se encontró el videojuego. Comprueba el nombre o intenta con otro título.",
                "usuario": usuario,
                "es_favorito": False,
                "en_biblioteca": False,
                "mensajes": obtener_flashes(request),
            },
        )

    es_favorito = fav_repo.es_favorito(correo, datos["nombre"]) if correo else False
    juego_id = datos.get("id") or datos.get("appid") or 0
    en_biblioteca = (bib_repo.obtener_por_id(correo, int(juego_id)) is not None) if (correo and juego_id) else False

    return templates.TemplateResponse(
        request=request,
        name="resultados.html",
        context={
            "juego": datos,
            "error": None,
            "usuario": usuario,
            "es_favorito": es_favorito,
            "en_biblioteca": en_biblioteca,
            "mensajes": obtener_flashes(request),
        },
    )


@router.get("/favoritos", response_class=HTMLResponse, name="favoritos")
def favoritos(
    request: Request,
    fav_repo: FavoritosRepository = Depends(get_favoritos_repo),
):
    correo = obtener_correo_sesion(request)
    if not correo:
        agregar_flash(request, "Debes iniciar sesión para ver tus favoritos.")
        return RedirectResponse(url=request.url_for("login"), status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="favoritos.html",
        context={
            "favoritos": fav_repo.obtener_por_usuario(correo),
            "usuario": obtener_usuario_sesion(request) or correo,
            "mensajes": obtener_flashes(request),
        },
    )


@router.post("/favoritos/agregar", name="agregar_favorito")
def agregar_favorito(
    request: Request,
    juego_json: str = Form("{}"),
    fav_repo: FavoritosRepository = Depends(get_favoritos_repo),
):
    correo = obtener_correo_sesion(request)
    if not correo:
        agregar_flash(request, "Debes iniciar sesión para guardar videojuegos.")
        return RedirectResponse(url=request.url_for("login"), status_code=303)

    try:
        datos_juego = json.loads(juego_json)
    except (json.JSONDecodeError, TypeError):
        agregar_flash(request, "No se pudieron leer los datos del videojuego.")
        return RedirectResponse(url=request.url_for("inicio"), status_code=303)

    if not isinstance(datos_juego, dict) or not datos_juego.get("nombre"):
        agregar_flash(request, "Los datos del videojuego están incompletos.")
        return RedirectResponse(url=request.url_for("inicio"), status_code=303)

    if fav_repo.agregar(correo, datos_juego):
        agregar_flash(request, "¡Videojuego agregado a tus favoritos!")
    else:
        agregar_flash(request, "Este videojuego ya está en tus favoritos.")

    query_str = urlencode({"q": datos_juego["nombre"]})
    return RedirectResponse(url=f"{request.url_for('resultados')}?{query_str}", status_code=303)


@router.post("/favoritos/eliminar", name="quitar_favorito")
def quitar_favorito(
    request: Request,
    nombre: str = Form(""),
    fav_repo: FavoritosRepository = Depends(get_favoritos_repo),
):
    correo = obtener_correo_sesion(request)
    if not correo:
        agregar_flash(request, "Debes iniciar sesión.")
        return RedirectResponse(url=request.url_for("login"), status_code=303)

    if nombre.strip():
        if fav_repo.eliminar(correo, nombre.strip()):
            agregar_flash(request, "Videojuego eliminado de tus favoritos.")
        else:
            agregar_flash(request, "No se encontró ese videojuego en tus favoritos.")

    return RedirectResponse(url=request.url_for("favoritos"), status_code=303)


@router.get("/biblioteca", response_class=HTMLResponse, name="biblioteca")
def vista_biblioteca(
    request: Request,
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
):
    correo = obtener_correo_sesion(request)
    if not correo:
        agregar_flash(request, "Debes iniciar sesión para acceder a tu biblioteca.")
        return RedirectResponse(url=request.url_for("login"), status_code=303)

    items = bib_repo.obtener_por_usuario(correo)
    return templates.TemplateResponse(
        request=request,
        name="biblioteca.html",
        context={
            "biblioteca": items,
            "correo": correo,
            "usuario": obtener_usuario_sesion(request) or correo,
            "mensajes": obtener_flashes(request),
        },
    )


@router.post("/biblioteca/agregar", name="agregar_biblioteca_form")
def agregar_biblioteca_form(
    request: Request,
    juego_json: str = Form("{}"),
    estado: str = Form("Por jugar"),
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
):
    correo = obtener_correo_sesion(request)
    if not correo:
        agregar_flash(request, "Debes iniciar sesión para agregar juegos a tu biblioteca.")
        return RedirectResponse(url=request.url_for("login"), status_code=303)

    try:
        datos_juego = json.loads(juego_json)
    except (json.JSONDecodeError, TypeError):
        agregar_flash(request, "No se pudieron leer los datos del videojuego.")
        return RedirectResponse(url=request.url_for("inicio"), status_code=303)

    juego_id = int(datos_juego.get("id") or datos_juego.get("appid") or 0)
    nombre = str(datos_juego.get("nombre", "")).strip()

    if not juego_id or not nombre:
        agregar_flash(request, "El videojuego no tiene un identificador válido.")
        return RedirectResponse(url=request.url_for("inicio"), status_code=303)

    item = BibliotecaItemCreate(
        juego_id=juego_id,
        nombre=nombre,
        estado=estado if estado in {"Por jugar", "Jugando", "Completado", "Abandonado"} else "Por jugar",
        juego=datos_juego,
    )

    if bib_repo.agregar(correo, item):
        agregar_flash(request, f"¡{nombre} agregado a tu biblioteca!")
    else:
        agregar_flash(request, f"{nombre} ya estaba en tu biblioteca.")

    query_str = urlencode({"q": nombre})
    return RedirectResponse(url=f"{request.url_for('resultados')}?{query_str}", status_code=303)