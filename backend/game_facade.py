from backend.config import ApiConfig
from backend.game_factory import GameEntityFactory, StandardGameFactory
from backend.http_client import HttpJsonClient
from backend.rawg_service import RawgService
from backend.score_strategy import RelacionCalidadPrecioStrategy, ScoreEvaluationStrategy
from backend.singleton import AppResourcesSingleton
from backend.steam_service import SteamService
from backend.translator_service import SinopsisTranslator


class GameCatalogFacade:
    """Patrón Facade: coordina RAWG, Steam, SteamSpy, traducción, Factory y Strategy."""

    def __init__(
        self,
        config: ApiConfig | None = None,
        http: HttpJsonClient | None = None,
        rawg: RawgService | None = None,
        steam: SteamService | None = None,
        translator: SinopsisTranslator | None = None,
        factory: GameEntityFactory | None = None,
        score_strategy: ScoreEvaluationStrategy | None = None,
    ):
        recursos = AppResourcesSingleton()
        self.config = config or recursos.config
        self.http = http or recursos.http_client
        self.rawg = rawg or RawgService(self.config, self.http)
        self.steam = steam or SteamService(self.config, self.http)
        self.translator = translator or SinopsisTranslator()
        self.factory = factory or StandardGameFactory()
        self.score_strategy = score_strategy or RelacionCalidadPrecioStrategy()

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

        analisis_compra = self.score_strategy.evaluar(
            rating_rawg=juego.get("rating"),
            metacritic=juego.get("metacritic"),
            precio_steam=precio,
            steamspy=steamspy,
        )

        return self.factory.crear_juego_completo(
            juego_rawg=juego,
            detalles_rawg=detalles,
            sinopsis=self.translator.obtener_sinopsis(detalles),
            screenshots=self.rawg.obtener_screenshots(game_id),
            gameplay=self.rawg.obtener_gameplay(game_id),
            appid=appid,
            precio_steam=precio,
            steamspy=steamspy,
            analisis_compra=analisis_compra,
        )