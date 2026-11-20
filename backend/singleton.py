from threading import Lock
from backend.config import ApiConfig
from backend.http_client import HttpJsonClient


class AppResourcesSingleton:
    """Patrón Singleton: garantiza una única instancia de configuración y cliente HTTP."""

    _instancia: "AppResourcesSingleton | None" = None
    _lock: Lock = Lock()

    def __new__(cls) -> "AppResourcesSingleton":
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    instancia = super().__new__(cls)
                    instancia.config = ApiConfig()
                    instancia.http_client = HttpJsonClient(
                        timeout=instancia.config.timeout_segundos,
                        reintentos=instancia.config.reintentos,
                    )
                    cls._instancia = instancia
        return cls._instancia