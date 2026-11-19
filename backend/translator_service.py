import html
import re
from deep_translator import GoogleTranslator


class SinopsisTranslator:
    """Limpia etiquetas HTML y traduce descripciones al español cuando hace falta."""

    def __init__(self, idioma_destino: str = "es", max_caracteres: int = 2500):
        self.idioma_destino = idioma_destino
        self.max_caracteres = max_caracteres

    @staticmethod
    def limpiar_html(texto: str) -> str:
        if not texto:
            return ""
        limpio = re.sub(r"<br\s*/?>", "\n", texto, flags=re.IGNORECASE)
        limpio = re.sub(r"</p\s*>", "\n", limpio, flags=re.IGNORECASE)
        limpio = re.sub(r"<[^>]*>", "", limpio)
        return html.unescape(limpio).strip()

    def traducir(self, texto: str) -> str:
        if not texto:
            return ""
        fragmento = texto[: self.max_caracteres]
        try:
            traducido = GoogleTranslator(source="auto", target=self.idioma_destino).translate(fragmento)
            return traducido if traducido else texto
        except Exception as error:
            print(f"Error de traduccion: {error}")
            return texto

    def obtener_sinopsis(self, detalles: dict | None) -> str:
        if not detalles:
            return "Sin descripcion disponible."

        raw = detalles.get("description") or detalles.get("description_raw") or ""
        texto = self.limpiar_html(raw)
        if not texto:
            return "Sin descripcion disponible."

        coincidencia = re.search(
            r"(?:^|\n)\s*(?:Español|Spanish)\s*:?\s*\n",
            texto,
            flags=re.IGNORECASE,
        )
        if coincidencia:
            en_espanol = texto[coincidencia.end():].strip()
            if en_espanol:
                return en_espanol

        return self.traducir(texto)