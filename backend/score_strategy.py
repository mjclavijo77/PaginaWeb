from abc import ABC, abstractmethod
from typing import Any


class ScoreEvaluationStrategy(ABC):
    """Patrón Strategy: contrato para calcular el índice de recomendación de compra."""

    @abstractmethod
    def evaluar(
        self,
        rating_rawg: float | None,
        metacritic: int | None,
        precio_steam: dict[str, Any] | None,
        steamspy: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise NotImplementedError


class RelacionCalidadPrecioStrategy(ScoreEvaluationStrategy):
    """Estrategia diferenciadora: cruza precio en COP, horas promedio (SteamSpy) y aprobación."""

    def evaluar(
        self,
        rating_rawg: float | None,
        metacritic: int | None,
        precio_steam: dict[str, Any] | None,
        steamspy: dict[str, Any] | None,
    ) -> dict[str, Any]:
        positivas = int((steamspy or {}).get("positivas") or 0)
        negativas = int((steamspy or {}).get("negativas") or 0)
        total_resenas = positivas + negativas
        aprobacion = round((positivas / total_resenas) * 100, 1) if total_resenas > 0 else None

        minutos_promedio = int((steamspy or {}).get("tiempo_promedio") or 0)
        horas_promedio = round(minutos_promedio / 60, 1) if minutos_promedio > 0 else None

        precio_info = (precio_steam or {}).get("precio") or {}
        # Steam devuelve 'final' en centavos (ej. 20190000 -> 201.900 COP)
        precio_cop = round((precio_info.get("final") or 0) / 100) if precio_info.get("final") else None
        descuento = int(precio_info.get("discount_percent") or 0)

        costo_por_hora = None
        if precio_cop and horas_promedio and horas_promedio > 0:
            costo_por_hora = round(precio_cop / horas_promedio)

        # Cálculo de puntaje GameFinder (0 a 100)
        puntaje = 50.0
        if aprobacion is not None:
            puntaje = (puntaje * 0.4) + (aprobacion * 0.6)
        elif rating_rawg:
            puntaje = (rating_rawg / 5.0) * 100

        if metacritic:
            puntaje = (puntaje * 0.7) + (metacritic * 0.3)

        if descuento >= 40:
            puntaje += 8
        elif descuento >= 20:
            puntaje += 4

        if costo_por_hora is not None:
            if costo_por_hora <= 2500:
                puntaje += 8
            elif costo_por_hora > 12000:
                puntaje -= 8

        puntaje_final = max(0, min(100, round(puntaje)))

        if puntaje_final >= 82:
            veredicto = "Compra muy recomendada"
            clase_badge = "excelente"
        elif puntaje_final >= 65:
            veredicto = "Buena opción (mejor en oferta)" if descuento == 0 else "Buena oferta actual"
            clase_badge = "buena"
        else:
            veredicto = "Espera un descuento fuerte"
            clase_badge = "esperar"

        return {
            "puntaje_gamefinder": puntaje_final,
            "veredicto": veredicto,
            "clase_badge": clase_badge,
            "aprobacion_porcentaje": aprobacion,
            "horas_promedio": horas_promedio,
            "costo_por_hora_cop": costo_por_hora,
            "descuento_actual": descuento,
        }