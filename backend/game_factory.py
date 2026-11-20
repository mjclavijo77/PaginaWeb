from abc import ABC, abstractmethod
from typing import Any


class GameEntityFactory(ABC):
    """Patrón Factory Method: contrato para construir entidades normalizadas de videojuegos."""

    @abstractmethod
    def crear_juego_completo(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError


class StandardGameFactory(GameEntityFactory):
    """Fábrica concreta que unifica los datos provenientes de RAWG, Steam y SteamSpy."""

    def crear_juego_completo(
        self,
        *,
        juego_rawg: dict[str, Any],
        detalles_rawg: dict[str, Any],
        sinopsis: str,
        screenshots: list[str],
        gameplay: str | None,
        appid: int | None,
        precio_steam: dict[str, Any] | None,
        steamspy: dict[str, Any] | None,
        analisis_compra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        plataformas = [
            p.get("platform", {}).get("name")
            for p in (juego_rawg.get("platforms") or [])
            if p.get("platform")
        ]
        generos = [g.get("name") for g in (juego_rawg.get("genres") or []) if g.get("name")]
        desarrolladores = [
            d.get("name")
            for d in (detalles_rawg.get("developers") or [])
            if d.get("name")
        ]
        esrb = detalles_rawg.get("esrb_rating") or {}

        return {
            "id": juego_rawg.get("id"),
            "nombre": detalles_rawg.get("name", juego_rawg.get("name")),
            "imagen": juego_rawg.get("background_image"),
            "rating": juego_rawg.get("rating"),
            "metacritic": juego_rawg.get("metacritic"),
            "lanzamiento": juego_rawg.get("released"),
            "generos": generos,
            "plataformas": plataformas,
            "desarrolladores": desarrolladores,
            "esrb": esrb.get("name"),
            "sitio_web": detalles_rawg.get("website"),
            "sinopsis": sinopsis,
            "screenshots": screenshots,
            "gameplay": gameplay,
            "appid": appid,
            "steam": precio_steam,
            "steamspy": steamspy,
            "steam_url": precio_steam.get("url") if precio_steam else None,
            "analisis_compra": analisis_compra,
        }