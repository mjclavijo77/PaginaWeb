from backend.config import ApiConfig
from backend.http_client import HttpJsonClient, normalizar_texto


class SteamService:
    """Consulta información de tienda en Steam y métricas en SteamSpy."""

    def __init__(self, config: ApiConfig, http: HttpJsonClient):
        self.config = config
        self.http = http

    def buscar_appid(self, nombre: str) -> int | None:
        datos = self.http.get_json(
            self.config.steam_search_url,
            {"term": nombre, "l": "spanish", "cc": "co"},
        )
        if not datos:
            return None

        busqueda = normalizar_texto(nombre)
        mejor = None
        mejor_puntaje = -1

        for item in datos.get("items", []):
            nombre_steam = normalizar_texto(item.get("name", ""))
            if nombre_steam == busqueda:
                puntaje = 100
            elif nombre_steam.startswith(busqueda):
                puntaje = 75
            elif busqueda in nombre_steam:
                puntaje = 55
            else:
                continue

            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor = item

        return mejor.get("id") if mejor else None

    def obtener_precio(self, appid: int | None) -> dict | None:
        if not appid:
            return None

        datos = self.http.get_json(
            self.config.steam_details_url,
            {"appids": appid, "cc": "co", "l": "spanish"},
        )
        if not datos:
            return None

        info = datos.get(str(appid), {})
        if not info.get("success"):
            return None

        juego = info.get("data", {})
        return {
            "nombre": juego.get("name"),
            "precio": juego.get("price_overview"),
            "imagen": juego.get("header_image"),
            "url": f"https://store.steampowered.com/app/{appid}/",
        }

    def obtener_estadisticas_steamspy(self, appid: int | None) -> dict | None:
        if not appid:
            return None

        datos = self.http.get_json(
            self.config.steamspy_url,
            {"request": "appdetails", "appid": appid},
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
            "tiempo_ultimas_dos_semanas": datos.get("average_2weeks"),
        }