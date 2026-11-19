from backend.config import ApiConfig
from backend.http_client import HttpJsonClient, normalizar_texto


class RawgService:
    """Encapsula la búsqueda, puntuación y consulta de detalles en RAWG."""

    ALIAS_SUGERENCIAS = {
        "gta": "Grand Theft Auto",
        "gta v": "Grand Theft Auto V",
        "gta 5": "Grand Theft Auto V",
        "gtav": "Grand Theft Auto V",
    }

    ALIAS_DETALLE = {
        "gta v": "Grand Theft Auto V",
        "gta 5": "Grand Theft Auto V",
        "gtav": "Grand Theft Auto V",
    }

    PALABRAS_NO_VALIDAS = {"demo", "beta", "prototype", "fan", "unofficial"}

    def __init__(self, config: ApiConfig, http: HttpJsonClient):
        self.config = config
        self.http = http

    def _validar_key(self) -> bool:
        if not self.config.rawg_api_key:
            print("Error: no se ha configurado RAWG_API_KEY en .env")
            return False
        return True

    def buscar_sugerencias(self, query: str, limite: int = 6, pagina: int = 1) -> list[dict]:
        if not self._validar_key():
            return []

        params = {
            "key": self.config.rawg_api_key,
            "page": max(1, pagina),
            "page_size": min(40, max(1, limite)),
        }

        if query and query.strip():
            clave = normalizar_texto(query)
            params["search"] = self.ALIAS_SUGERENCIAS.get(clave, query.strip())

        datos = self.http.get_json(f"{self.config.rawg_base_url}/games", params=params, intentos=2)
        if not datos:
            return []

        sugerencias = []
        for item in datos.get("results", []):
            nombre = item.get("name", "")
            palabras = set(normalizar_texto(nombre).split())
            if self.PALABRAS_NO_VALIDAS.intersection(palabras):
                continue

            generos = [g.get("name") for g in (item.get("genres") or []) if g.get("name")]
            lanzamiento = item.get("released") or ""

            sugerencias.append({
                "id": item.get("id"),
                "nombre": nombre,
                "genero": generos[0] if generos else "Videojuego",
                "generos": generos,
                "anio": lanzamiento[:4] if len(lanzamiento) >= 4 else "",
                "rating": item.get("rating"),
                "imagen": item.get("background_image"),
            })

            if len(sugerencias) >= limite:
                break

        return sugerencias

    def _puntuar_candidato(self, juego: dict, busqueda: str) -> float | None:
        nombre_resultado = normalizar_texto(juego.get("name", ""))
        palabras = set(nombre_resultado.split())

        if self.PALABRAS_NO_VALIDAS.intersection(palabras):
            return None

        puntuacion = 0.0
        if nombre_resultado == busqueda:
            puntuacion += 200
        elif nombre_resultado.startswith(busqueda):
            puntuacion += 140
        elif busqueda in nombre_resultado:
            puntuacion += 90
        else:
            coincidencias = set(busqueda.split()).intersection(palabras)
            if not coincidencias:
                return None
            puntuacion += (len(coincidencias) / len(busqueda.split())) * 60

        puntuacion += min((juego.get("ratings_count") or 0) / 500, 25)
        if juego.get("metacritic"):
            puntuacion += 10

        tiendas = juego.get("stores") or []
        if any(t.get("store", {}).get("slug") == "steam" for t in tiendas):
            puntuacion += 20
        if any(t.get("store", {}).get("slug") == "itch" for t in tiendas):
            puntuacion -= 50

        return puntuacion

    def buscar_mejor_juego(self, nombre: str) -> dict | None:
        if not self._validar_key():
            return None

        busqueda_original = normalizar_texto(nombre)
        nombre_busqueda = self.ALIAS_DETALLE.get(busqueda_original, nombre)
        busqueda = normalizar_texto(nombre_busqueda)

        consultas = [nombre_busqueda]
        if busqueda_original != busqueda:
            consultas.append(nombre)

        candidatos = {}
        for consulta in consultas:
            datos = self.http.get_json(
                f"{self.config.rawg_base_url}/games",
                {
                    "key": self.config.rawg_api_key,
                    "search": consulta,
                    "page_size": 40,
                    "search_precise": "true",
                },
            )
            if datos:
                for juego in datos.get("results", []):
                    candidatos[juego.get("id")] = juego

        if not candidatos:
            return None

        mejor_juego = None
        mejor_puntaje = float("-inf")

        for juego in candidatos.values():
            puntaje = self._puntuar_candidato(juego, busqueda)
            if puntaje is not None and puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_juego = juego

        return mejor_juego

    def obtener_detalles(self, game_id: int) -> dict | None:
        return self.http.get_json(
            f"{self.config.rawg_base_url}/games/{game_id}",
            {"key": self.config.rawg_api_key},
        )

    def obtener_screenshots(self, game_id: int) -> list[str]:
        datos = self.http.get_json(
            f"{self.config.rawg_base_url}/games/{game_id}/screenshots",
            {"key": self.config.rawg_api_key},
        )
        if not datos:
            return []
        return [c.get("image") for c in datos.get("results", []) if c.get("image")]

    def obtener_gameplay(self, game_id: int) -> str | None:
        datos = self.http.get_json(
            f"{self.config.rawg_base_url}/games/{game_id}/movies",
            {"key": self.config.rawg_api_key},
        )
        if not datos:
            return None
        videos = datos.get("results", [])
        if videos:
            return videos[0].get("data", {}).get("max")
        return None