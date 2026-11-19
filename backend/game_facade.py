from backend.config import ApiConfig
from backend.http_client import HttpJsonClient
from backend.rawg_service import RawgService
from backend.steam_service import SteamService
from backend.translator_service import SinopsisTranslator


class GameCatalogFacade:
    """Fachada que coordina RAWG, Steam, SteamSpy y traducción de sinopsis."""

    def __init__(
        self,
        config: ApiConfig | None = None,
        http: HttpJsonClient | None = None,
        rawg: RawgService | None = None,
        steam: SteamService | None = None,
        translator: SinopsisTranslator | None = None,
    ):
        self.config = config or ApiConfig()
        self.http = http or HttpJsonClient(
            timeout=self.config.timeout_segundos,
            reintentos=self.config.reintentos,
        )
        self.rawg = rawg or RawgService(self.config, self.http)
        self.steam = steam or SteamService(self.config, self.http)
        self.translator = translator or SinopsisTranslator()

    def buscar_sugerencias(self, query: str, limite: int = 6, pagina: int = 1) -> list[dict]:
        return self.rawg.buscar_sugerencias(query=query, limite=limite, pagina=pagina)

    def obtener_datos_completos(self, nombre_juego: str) -> dict | None:
        juego = self.rawg.buscar_mejor_juego(nombre_juego)
        if not juego:
            return None

        game_id = juego.get("id")
        detalles = self.rawg.obtener_detalles(game_id) or juego

        nombre_encontrado = juego.get("name", nombre_juego)
        appid = self.steam.buscar_appid(nombre_encontrado)
        precio = self.steam.obtener_precio(appid)
        steamspy = self.steam.obtener_estadisticas_steamspy(appid)

        plataformas = [
            p.get("platform", {}).get("name")
            for p in (juego.get("platforms") or [])
            if p.get("platform")
        ]
        generos = [g.get("name") for g in (juego.get("genres") or []) if g.get("name")]
        desarrolladores = [
            d.get("name")
            for d in (detalles.get("developers") or [])
            if d.get("name")
        ]
        esrb = detalles.get("esrb_rating") or {}

        return {
            "nombre": detalles.get("name", juego.get("name")),
            "imagen": juego.get("background_image"),
            "rating": juego.get("rating"),
            "metacritic": juego.get("metacritic"),
            "lanzamiento": juego.get("released"),
            "generos": generos,
            "plataformas": plataformas,
            "desarrolladores": desarrolladores,
            "esrb": esrb.get("name"),
            "sitio_web": detalles.get("website"),
            "sinopsis": self.translator.obtener_sinopsis(detalles),
            "screenshots": self.rawg.obtener_screenshots(game_id),
            "gameplay": self.rawg.obtener_gameplay(game_id),
            "appid": appid,
            "steam": precio,
            "steamspy": steamspy,
            "steam_url": precio.get("url") if precio else None,
        }