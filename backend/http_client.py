import re
import time
import unicodedata
import requests


class HttpJsonClient:
    """Cliente HTTP reutilizable con reintentos básicos."""

    def __init__(self, timeout: int = 15, reintentos: int = 3):
        self.timeout = timeout
        self.reintentos = reintentos

    def get_json(self, url: str, params: dict | None = None, intentos: int | None = None) -> dict | None:
        max_intentos = intentos if intentos is not None else self.reintentos

        for intento in range(max_intentos):
            try:
                respuesta = requests.get(url, params=params, timeout=self.timeout)
                respuesta.raise_for_status()
                return respuesta.json()
            except requests.RequestException as error:
                print(f"Error de conexion ({intento + 1}/{max_intentos}): {error}")
                if intento < max_intentos - 1:
                    time.sleep(1)

        return None


def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    normalizado = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    minusculas = sin_acentos.lower()
    solo_alfanumerico = re.sub(r"[^a-z0-9 ]", " ", minusculas)
    return re.sub(r"\s+", " ", solo_alfanumerico).strip()