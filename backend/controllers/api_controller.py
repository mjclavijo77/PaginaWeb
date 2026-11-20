import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status

from backend.controllers.dependencies import (
    get_biblioteca_repo,
    get_catalogo_facade,
    get_user_repo,
    obtener_correo_sesion,
)
from backend.game_facade import GameCatalogFacade
from backend.models.schemas import (
    BibliotecaEstadoPatch,
    BibliotecaItemCreate,
    BibliotecaItemUpdate,
)
from backend.repositories import BibliotecaRepository, UserRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["API REST (Swagger & Fetch)"])


def _resolver_correo(request: Request, correo_query: str | None, user_repo: UserRepository) -> str:
    """Permite usar la sesión activa del navegador o enviar ?correo=... directamente desde Swagger."""
    correo = obtener_correo_sesion(request) or (correo_query.strip().lower() if correo_query else None)
    if not correo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inicia sesión en la web o envía el parámetro 'correo' en Swagger.",
        )
    if not user_repo.buscar_por_correo(correo):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario '{correo}' no existe.",
        )
    return correo



# ENDPOINTS GET DE CATÁLOGO Y BÚSQUEDA


@router.get("/buscar", summary="Buscar sugerencias rápidas de videojuegos")
def buscar_juegos(
    q: str = Query(default="", description="Texto a buscar"),
    limite: int = Query(default=6, ge=1, le=12),
    catalogo: GameCatalogFacade = Depends(get_catalogo_facade),
):
    query = q.strip()
    if len(query) < 2:
        return []

    try:
        return catalogo.buscar_sugerencias(query=query, limite=limite)
    except Exception:
        logger.exception("Error al buscar sugerencias.")
        raise HTTPException(status_code=500, detail="Error al consultar sugerencias.")


@router.get("/videojuegos", summary="Consultar catálogo paginado de videojuegos")
def api_videojuegos(
    q: str = Query(default=""),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=40),
    catalogo: GameCatalogFacade = Depends(get_catalogo_facade),
):
    try:
        juegos = catalogo.buscar_sugerencias(query=q.strip(), limite=tamano, pagina=pagina)
        return {
            "pagina": pagina,
            "cantidad": len(juegos),
            "videojuegos": juegos,
        }
    except Exception:
        logger.exception("Error al consultar el catálogo.")
        raise HTTPException(status_code=500, detail="No fue posible consultar el catálogo.")


@router.get("/videojuegos/{nombre_juego}", summary="Obtener detalle completo e Índice GameFinder por nombre (Path Param)")
def api_detalle_videojuego(
    nombre_juego: str = Path(..., min_length=1, examples=["Halo"]),
    catalogo: GameCatalogFacade = Depends(get_catalogo_facade),
):
    datos = catalogo.obtener_datos_completos(nombre_juego.strip())
    if not datos:
        raise HTTPException(status_code=404, detail=f"No se encontró el videojuego '{nombre_juego}'.")
    return datos



# ENDPOINTS CRUD BIBLIOTECA (GET, POST, PUT, PATCH, DELETE + PATH PARAMS)


@router.get("/biblioteca", summary="GET - Listar todos los juegos en la biblioteca del usuario")
def listar_biblioteca(
    request: Request,
    correo: str | None = Query(default=None, description="Correo del usuario (opcional si ya inició sesión)"),
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    correo_usuario = _resolver_correo(request, correo, user_repo)
    items = bib_repo.obtener_por_usuario(correo_usuario)
    return {"correo": correo_usuario, "total": len(items), "biblioteca": items}


@router.get("/biblioteca/{juego_id}", summary="GET - Consultar un juego específico de la biblioteca por ID (Path Param)")
def obtener_juego_biblioteca(
    request: Request,
    juego_id: int = Path(..., ge=1, examples=[1245620]),
    correo: str | None = Query(default=None),
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    correo_usuario = _resolver_correo(request, correo, user_repo)
    item = bib_repo.obtener_por_id(correo_usuario, juego_id)
    if not item:
        raise HTTPException(status_code=404, detail="El juego no está en tu biblioteca.")
    return item


@router.post("/biblioteca", status_code=status.HTTP_201_CREATED, summary="POST - Agregar un juego a la biblioteca")
def agregar_juego_biblioteca(
    request: Request,
    payload: BibliotecaItemCreate,
    correo: str | None = Query(default=None),
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    correo_usuario = _resolver_correo(request, correo, user_repo)
    creado = bib_repo.agregar(correo_usuario, payload)
    if not creado:
        raise HTTPException(status_code=409, detail="Este juego ya existe en tu biblioteca.")
    return {"mensaje": "Videojuego agregado a la biblioteca.", "item": creado}


@router.put("/biblioteca/{juego_id}", summary="PUT - Reemplazar estado, calificación y notas de un juego (Path Param)")
def reemplazar_juego_biblioteca(
    request: Request,
    payload: BibliotecaItemUpdate,
    juego_id: int = Path(..., ge=1, examples=[1245620]),
    correo: str | None = Query(default=None),
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    correo_usuario = _resolver_correo(request, correo, user_repo)
    actualizado = bib_repo.reemplazar(correo_usuario, juego_id, payload)
    if not actualizado:
        raise HTTPException(status_code=404, detail="El juego no existe en tu biblioteca.")
    return {"mensaje": "Registro reemplazado correctamente (PUT).", "item": actualizado}


@router.patch("/biblioteca/{juego_id}", summary="PATCH - Actualizar parcialmente estado, nota o calificación (Path Param)")
def actualizar_parcial_biblioteca(
    request: Request,
    payload: BibliotecaEstadoPatch,
    juego_id: int = Path(..., ge=1, examples=[1245620]),
    correo: str | None = Query(default=None),
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    correo_usuario = _resolver_correo(request, correo, user_repo)
    actualizado = bib_repo.actualizar_parcial(correo_usuario, juego_id, payload)
    if not actualizado:
        raise HTTPException(status_code=404, detail="El juego no existe en tu biblioteca.")
    return {"mensaje": "Registro actualizado parcialmente (PATCH).", "item": actualizado}


@router.delete("/biblioteca/{juego_id}", summary="DELETE - Eliminar un juego de la biblioteca (Path Param)")
def eliminar_juego_biblioteca(
    request: Request,
    juego_id: int = Path(..., ge=1, examples=[1245620]),
    correo: str | None = Query(default=None),
    bib_repo: BibliotecaRepository = Depends(get_biblioteca_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    correo_usuario = _resolver_correo(request, correo, user_repo)
    eliminado = bib_repo.eliminar(correo_usuario, juego_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="El juego no existe en tu biblioteca.")
    return {"mensaje": f"Juego {juego_id} eliminado de la biblioteca."}