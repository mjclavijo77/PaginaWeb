import json
from pathlib import Path
from typing import Any


class JsonFileStorage:
    """Encapsula la lectura y escritura atómica en archivos JSON."""

    def __init__(self, ruta_archivo: Path):
        self.ruta = ruta_archivo

    def leer(self, valor_por_defecto: Any = None) -> Any:
        if valor_por_defecto is None:
            valor_por_defecto = []

        if not self.ruta.exists():
            return valor_por_defecto

        try:
            with self.ruta.open("r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except (json.JSONDecodeError, OSError):
            return valor_por_defecto

    def escribir(self, datos: Any) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.ruta.with_suffix(self.ruta.suffix + ".tmp")

        with temporal.open("w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)

        temporal.replace(self.ruta)