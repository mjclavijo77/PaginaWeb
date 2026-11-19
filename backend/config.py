import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ApiConfig:
    rawg_api_key: str = os.getenv("RAWG_API_KEY", "").strip()
    steam_api_key: str = os.getenv("STEAM_API_KEY", "").strip()
    rawg_base_url: str = "https://api.rawg.io/api"
    steam_search_url: str = "https://store.steampowered.com/api/storesearch/"
    steam_details_url: str = "https://store.steampowered.com/api/appdetails"
    steamspy_url: str = "https://steamspy.com/api.php"
    timeout_segundos: int = 15
    reintentos: int = 3