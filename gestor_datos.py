
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ARCHIVO_USUARIOS = BASE_DIR / "usuarios.json"
ARCHIVO_JUEGOS = BASE_DIR / "juegos.json"
ARCHIVO_FAVORITOS = BASE_DIR / "favoritos.json"


def leer_json(ruta, valor_por_defecto):
    if not ruta.exists():
        return valor_por_defecto

    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except (json.JSONDecodeError, OSError):
        return valor_por_defecto


def guardar_json(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)

    temporal = ruta.with_suffix(ruta.suffix + ".tmp")

    with temporal.open("w", encoding="utf-8") as archivo:
        json.dump(
            datos,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    temporal.replace(ruta)


def cargar_juegos():
    datos = leer_json(ARCHIVO_JUEGOS, [])
    return datos if isinstance(datos, list) else []


def cargar_usuarios():
    datos = leer_json(ARCHIVO_USUARIOS, [])
    return datos if isinstance(datos, list) else []


def guardar_usuario(datos_usuario):
    usuarios = cargar_usuarios()

    correo = str(datos_usuario.get("correo", "")).strip().lower()

    if not correo:
        return False

    if any(
        str(usuario.get("correo", "")).strip().lower() == correo
        for usuario in usuarios
    ):
        return False

    nuevo = dict(datos_usuario)
    nuevo["correo"] = correo

    usuarios.append(nuevo)
    guardar_json(ARCHIVO_USUARIOS, usuarios)

    return True


def validar_usuario(correo, password):
    correo = correo.strip().lower()

    for usuario in cargar_usuarios():
        if (
            str(usuario.get("correo", "")).strip().lower() == correo
            and usuario.get("password") == password
        ):
            return usuario

    return None


def cargar_favoritos():
    datos = leer_json(ARCHIVO_FAVORITOS, [])
    return datos if isinstance(datos, list) else []


def obtener_favoritos(correo):
    correo = correo.strip().lower()

    return [
        favorito
        for favorito in cargar_favoritos()
        if str(favorito.get("correo", "")).strip().lower() == correo
    ]


def guardar_favorito(correo, juego):
    if not isinstance(juego, dict):
        return False

    correo = correo.strip().lower()
    nombre = str(juego.get("nombre", "")).strip()

    if not correo or not nombre:
        return False

    favoritos = cargar_favoritos()

    for favorito in favoritos:
        if (
            str(favorito.get("correo", "")).strip().lower() == correo
            and str(favorito.get("nombre", "")).strip().casefold()
            == nombre.casefold()
        ):
            return False

    favoritos.append({
        "correo": correo,
        "nombre": nombre,
        "juego": juego
    })

    guardar_json(ARCHIVO_FAVORITOS, favoritos)

    return True


def eliminar_favorito(correo, nombre):
    correo = correo.strip().lower()
    nombre = nombre.strip().casefold()

    favoritos = cargar_favoritos()

    restantes = [
        favorito
        for favorito in favoritos
        if not (
            str(favorito.get("correo", "")).strip().lower() == correo
            and str(favorito.get("nombre", "")).strip().casefold() == nombre
        )
    ]

    if len(restantes) == len(favoritos):
        return False

    guardar_json(ARCHIVO_FAVORITOS, restantes)

    return True


def comprobar_favorito(correo, nombre):
    nombre = nombre.strip().casefold()

    return any(
        str(favorito.get("nombre", "")).strip().casefold() == nombre
        for favorito in obtener_favoritos(correo)
    )
