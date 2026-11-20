from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


EstadoJuego = Literal["Por jugar", "Jugando", "Completado", "Abandonado"]


class UsuarioCreate(BaseModel):
    correo: str = Field(..., min_length=5, examples=["usuario@ejemplo.com"])
    usuario: str = Field(..., min_length=2, max_length=40, examples=["GamerPro"])
    password: str = Field(..., min_length=6, examples=["123456"])


class UsuarioLogin(BaseModel):
    correo: str
    password: str


class UsuarioDB(BaseModel):
    correo: str
    usuario: str
    password_hash: str


class FavoritoItem(BaseModel):
    correo: str
    nombre: str
    juego: dict[str, Any]


class BibliotecaItemCreate(BaseModel):
    juego_id: int = Field(..., examples=[1245620])
    nombre: str = Field(..., min_length=1, examples=["Elden Ring"])
    estado: EstadoJuego = "Por jugar"
    calificacion_personal: int | None = Field(default=None, ge=1, le=10, examples=[9])
    notas: str = Field(default="", max_length=500, examples=["Jefe final pendiente"])
    juego: dict[str, Any] = Field(default_factory=dict)


class BibliotecaItemUpdate(BaseModel):
    """Para peticiones PUT (reemplazo completo de metadatos editables)."""
    estado: EstadoJuego
    calificacion_personal: int | None = Field(default=None, ge=1, le=10)
    notas: str = Field(default="", max_length=500)


class BibliotecaEstadoPatch(BaseModel):
    """Para peticiones PATCH (actualización parcial rápida)."""
    estado: EstadoJuego | None = None
    calificacion_personal: int | None = Field(default=None, ge=1, le=10)
    notas: str | None = Field(default=None, max_length=500)


class BibliotecaItemDB(BaseModel):
    correo: str
    juego_id: int
    nombre: str
    estado: EstadoJuego = "Por jugar"
    calificacion_personal: int | None = None
    notas: str = ""
    fecha_agregado: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    juego: dict[str, Any] = Field(default_factory=dict)