
import os
import re
import time
import html
import unicodedata
import requests

from pathlib import Path
from dotenv import load_dotenv
from deep_translator import GoogleTranslator


# =====================================================
# CONFIGURACION
# =====================================================

RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(RUTA_ENV)

RAWG_API_KEY = os.getenv("RAWG_API_KEY")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

RAWG_URL = "https://api.rawg.io/api"
STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
STEAMSPY_URL = "https://steamspy.com/api.php"


# =====================================================
# FUNCIONES GENERALES
# =====================================================

def get_con_reintento(url, params=None, intentos=3):

    for intento in range(intentos):

        try:
            respuesta = requests.get(
                url,
                params=params,
                timeout=15
            )

            respuesta.raise_for_status()

            return respuesta.json()

        except requests.RequestException as error:

            print(
                f"Error de conexion ({intento + 1}/{intentos}): {error}"
            )

            if intento < intentos - 1:
                time.sleep(1)

    return None


def normalizar_nombre(nombre):

    nombre = unicodedata.normalize("NFKD", nombre)

    nombre = "".join(
        c for c in nombre
        if not unicodedata.combining(c)
    )

    nombre = nombre.lower()

    nombre = re.sub(r"[^a-z0-9 ]", " ", nombre)

    return re.sub(r"\s+", " ", nombre).strip()


# =====================================================
# TRADUCCION Y SINOPSIS
# =====================================================

def traducir_a_espanol(texto):

    if not texto:
        return ""

    partes = re.split(r"(?<=[.!?])\s+", texto.strip())

    bloques = []
    bloque_actual = ""

    for parte in partes:

        if not parte:
            continue

        if len(bloque_actual) + len(parte) + 1 <= 4000:
            bloque_actual = f"{bloque_actual} {parte}".strip()

        else:

            if bloque_actual:
                bloques.append(bloque_actual)

            bloque_actual = parte

    if bloque_actual:
        bloques.append(bloque_actual)

    traducciones = []

    for bloque in bloques:

        traducido = None

        for intento in range(3):

            try:

                traducido = GoogleTranslator(
                    source="auto",
                    target="es"
                ).translate(bloque)

                if traducido:
                    break

            except Exception as error:

                print(
                    f"Error de traduccion ({intento + 1}/3): {error}"
                )

                if intento < 2:
                    time.sleep(2 * (intento + 1))

        if not traducido:

            print("No fue posible traducir la descripcion.")

            return None

        traducciones.append(traducido)

    return "\n".join(traducciones)


def limpiar_sinopsis(texto):

    if not texto:
        return ""

    texto = re.sub(
        r"<br\s*/?>",
        "\n",
        texto,
        flags=re.IGNORECASE
    )

    texto = re.sub(
        r"</p\s*>",
        "\n",
        texto,
        flags=re.IGNORECASE
    )

    texto = re.sub(r"<[^>]*>", "", texto)

    texto = html.unescape(texto)

    return texto.strip()


def obtener_sinopsis(detalles, descripcion_steam=None):

    if not detalles:

        return (
            limpiar_sinopsis(descripcion_steam)
            or "Descripcion no disponible en español."
        )

    descripcion = (
        detalles.get("description")
        or detalles.get("description_raw")
        or ""
    )

    descripcion = limpiar_sinopsis(descripcion)

    if descripcion:

        coincidencia = re.search(
            r"(?:^|\n)\s*(?:Español|Spanish)\s*:?\s*\n",
            descripcion,
            flags=re.IGNORECASE
        )

        if coincidencia:

            descripcion_espanol = descripcion[
                coincidencia.end():
            ].strip()

            if descripcion_espanol:

                print(
                    "Se encontro una descripcion en español en RAWG."
                )

                return descripcion_espanol

        traducido = traducir_a_espanol(descripcion)

        if traducido:
            return traducido

    descripcion_steam = limpiar_sinopsis(descripcion_steam)

    if descripcion_steam:

        print(
            "Se utilizara la descripcion en español de Steam."
        )

        return descripcion_steam

    return (
        "La descripcion no esta disponible en español en este momento."
    )


# =====================================================
# RAWG: BUSQUEDA
# =====================================================

def obtener_juego_rawg(nombre):

    if not RAWG_API_KEY:

        print("Error: no se ha configurado RAWG_API_KEY.")

        return None

    alias = {
        "gta v": "Grand Theft Auto V",
        "gta 5": "Grand Theft Auto V",
        "gtav": "Grand Theft Auto V"
    }

    busqueda_original = normalizar_nombre(nombre)

    nombre_busqueda = alias.get(
        busqueda_original,
        nombre
    )

    busqueda = normalizar_nombre(nombre_busqueda)

    consultas = [nombre_busqueda]

    if busqueda_original != busqueda:
        consultas.append(nombre)

    juegos = {}

    for consulta in consultas:

        datos = get_con_reintento(
            f"{RAWG_URL}/games",
            {
                "key": RAWG_API_KEY,
                "search": consulta,
                "page_size": 40,
                "search_precise": "true"
            }
        )

        if datos:

            for juego in datos.get("results", []):

                juegos[juego.get("id")] = juego

    if not juegos:

        print("No se encontraron resultados en RAWG.")

        return None

    palabras_no_validas = {
        "demo",
        "beta",
        "prototype",
        "fan",
        "unofficial"
    }

    mejor_juego = None

    mejor_puntuacion = float("-inf")

    for juego in juegos.values():

        nombre_resultado = normalizar_nombre(
            juego.get("name", "")
        )

        palabras = set(nombre_resultado.split())

        if palabras_no_validas.intersection(palabras):
            continue

        puntuacion = 0

        if nombre_resultado == busqueda:
            puntuacion += 200

        elif nombre_resultado.startswith(busqueda):
            puntuacion += 140

        elif busqueda in nombre_resultado:
            puntuacion += 90

        else:

            coincidencias = (
                set(busqueda.split()).intersection(palabras)
            )

            if not coincidencias:
                continue

            puntuacion += (
                len(coincidencias)
                / max(len(busqueda.split()), 1)
                * 60
            )

        puntuacion += min(
            juego.get("ratings_count", 0) / 500,
            25
        )

        if juego.get("metacritic"):
            puntuacion += 10

        tiendas = juego.get("stores") or []

        if any(
            t.get("store", {}).get("slug") == "steam"
            for t in tiendas
        ):
            puntuacion += 20

        if any(
            t.get("store", {}).get("slug") == "itch"
            for t in tiendas
        ):
            puntuacion -= 50

        if puntuacion > mejor_puntuacion:

            mejor_puntuacion = puntuacion

            mejor_juego = juego

    if mejor_juego and mejor_puntuacion < 60:

        print(
            "La coincidencia encontrada no es suficientemente precisa."
        )

        return None

    if mejor_juego:

        nombre_resultado = normalizar_nombre(
            mejor_juego.get("name", "")
        )

        palabras_consulta = set(busqueda.split())

        palabras_resultado = set(
            nombre_resultado.split()
        )

        cobertura = (
            len(
                palabras_consulta.intersection(
                    palabras_resultado
                )
            )
            / max(len(palabras_consulta), 1)
        )

        if nombre_resultado != busqueda and cobertura < 0.60:

            print(
                "No se encontro una coincidencia suficientemente cercana."
            )

            return None

        print(
            f"Juego encontrado: {mejor_juego.get('name')}"
        )

    else:

        print("No se encontro un resultado adecuado.")

    return mejor_juego


# =====================================================
# RAWG: DETALLES
# =====================================================

def obtener_detalles_rawg(game_id):

    return get_con_reintento(
        f"{RAWG_URL}/games/{game_id}",
        {"key": RAWG_API_KEY}
    )


def obtener_screenshots(game_id):

    datos = get_con_reintento(
        f"{RAWG_URL}/games/{game_id}/screenshots",
        {"key": RAWG_API_KEY}
    )

    if not datos:
        return []

    return [
        captura.get("image")
        for captura in datos.get("results", [])
        if captura.get("image")
    ]


def obtener_gameplay(game_id):

    datos = get_con_reintento(
        f"{RAWG_URL}/games/{game_id}/movies",
        {"key": RAWG_API_KEY}
    )

    if not datos:
        return None

    videos = datos.get("results", [])

    if videos:
        return videos[0].get("data", {}).get("max")

    return None


# =====================================================
# STEAM: BUSQUEDA Y PRECIO
# =====================================================

def obtener_steam_id(nombre):

    datos = get_con_reintento(
        STEAM_SEARCH_URL,
        {
            "term": nombre,
            "l": "spanish",
            "cc": "co"
        }
    )

    if not datos:
        return None

    resultados = datos.get("items", [])

    busqueda = normalizar_nombre(nombre)

    mejor_resultado = None

    mejor_puntuacion = -1

    for juego in resultados:

        nombre_steam = normalizar_nombre(
            juego.get("name", "")
        )

        if nombre_steam == busqueda:
            puntuacion = 100

        elif nombre_steam.startswith(busqueda):
            puntuacion = 75

        elif busqueda in nombre_steam:
            puntuacion = 55

        else:
            continue

        if puntuacion > mejor_puntuacion:

            mejor_puntuacion = puntuacion

            mejor_resultado = juego

    return (
        mejor_resultado.get("id")
        if mejor_resultado
        else None
    )


def obtener_precio_steam(appid):

    if not appid:
        return None

    datos = get_con_reintento(
        STEAM_DETAILS_URL,
        {
            "appids": appid,
            "cc": "co",
            "l": "spanish"
        }
    )

    if not datos:
        return None

    informacion = datos.get(str(appid), {})

    if not informacion.get("success"):
        return None

    juego = informacion.get("data", {})

    return {
        "nombre": juego.get("name"),
        "precio": juego.get("price_overview"),
        "imagen": juego.get("header_image"),
        "descripcion": juego.get("short_description"),
        "url": f"https://store.steampowered.com/app/{appid}/"
    }


# =====================================================
# STEAMSPY: ESTADISTICAS
# =====================================================

def obtener_steamspy(appid):

    if not appid:
        return None

    datos = get_con_reintento(
        STEAMSPY_URL,
        {
            "request": "appdetails",
            "appid": appid
        }
    )

    if not datos:
        return None

    positivas = int(datos.get("positive", 0) or 0)

    negativas = int(datos.get("negative", 0) or 0)

    return {
        "propietarios": datos.get("owners"),
        "reseñas": positivas + negativas,
        "positivas": positivas,
        "negativas": negativas,
        "tiempo_promedio": datos.get("average_forever"),
        "tiempo_ultimas_dos_semanas": datos.get("average_2weeks")
    }


# =====================================================
# INTEGRACION DE LAS API
# =====================================================

def obtener_datos_completos(nombre_juego):

    print(f"Buscando videojuego: {nombre_juego}")

    juego = obtener_juego_rawg(nombre_juego)

    if not juego:

        print("No se encontro el videojuego en RAWG.")

        return None

    game_id = juego.get("id")

    detalles = obtener_detalles_rawg(game_id) or juego

    nombre_encontrado = juego.get(
        "name",
        nombre_juego
    )

    appid = obtener_steam_id(nombre_encontrado)

    precio = obtener_precio_steam(appid)

    steamspy = obtener_steamspy(appid)

    plataformas = [
        p.get("platform", {}).get("name")
        for p in juego.get("platforms", [])
    ]

    generos = [
        g.get("name")
        for g in juego.get("genres", [])
    ]

    desarrolladores = [
        d.get("name")
        for d in detalles.get("developers", [])
    ]

    esrb = detalles.get("esrb_rating") or {}

    return {
        "nombre": detalles.get(
            "name",
            juego.get("name")
        ),
        "imagen": juego.get("background_image"),
        "rating": juego.get("rating"),
        "metacritic": juego.get("metacritic"),
        "lanzamiento": juego.get("released"),
        "generos": generos,
        "plataformas": plataformas,
        "desarrolladores": desarrolladores,
        "esrb": esrb.get("name"),
        "sitio_web": detalles.get("website"),
        "sinopsis": obtener_sinopsis(
            detalles,
            precio.get("descripcion") if precio else None
        ),
        "screenshots": obtener_screenshots(game_id),
        "gameplay": obtener_gameplay(game_id),
        "appid": appid,
        "steam": precio,
        "steamspy": steamspy,
        "steam_url": precio.get("url") if precio else None
    }
