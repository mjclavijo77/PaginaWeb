import hashlib
import hmac
import secrets
from pathlib import Path

from backend.models.schemas import UsuarioCreate, UsuarioDB
from backend.repositories.base import IReadableRepository, IWritableRepository
from backend.repositories.json_storage import JsonFileStorage


class UserRepository(IReadableRepository[dict], IWritableRepository[dict]):
    """Gestiona la persistencia y verificación de credenciales de usuarios."""

    def __init__(self, ruta_archivo: Path):
        self.storage = JsonFileStorage(ruta_archivo)

    @staticmethod
    def hashear_password(password: str, salt: str | None = None) -> str:
        salt_actual = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt_actual.encode("utf-8"),
            100_000,
        ).hex()
        return f"pbkdf2_sha256${salt_actual}${digest}"

    @classmethod
    def verificar_password(cls, password_plana: str, almacenada: str) -> bool:
        if almacenada.startswith("pbkdf2_sha256$"):
            try:
                _, salt, _ = almacenada.split("$", 2)
                esperado = cls.hashear_password(password_plana, salt=salt)
                return hmac.compare_digest(esperado, almacenada)
            except ValueError:
                return False
        # Compatibilidad con usuarios antiguos guardados en texto plano
        return hmac.compare_digest(password_plana, almacenada)

    def listar_todos(self) -> list[dict]:
        datos = self.storage.leer([])
        return datos if isinstance(datos, list) else []

    def guardar_todos(self, items: list[dict]) -> None:
        self.storage.escribir(items)

    def buscar_por_correo(self, correo: str) -> dict | None:
        correo_norm = correo.strip().lower()
        for usuario in self.listar_todos():
            if str(usuario.get("correo", "")).strip().lower() == correo_norm:
                return usuario
        return None

    def crear_usuario(self, datos: UsuarioCreate) -> UsuarioDB | None:
        correo_norm = datos.correo.strip().lower()
        if not correo_norm or self.buscar_por_correo(correo_norm):
            return None

        usuarios = self.listar_todos()
        nuevo = UsuarioDB(
            correo=correo_norm,
            usuario=datos.usuario.strip(),
            password_hash=self.hashear_password(datos.password),
        )
        usuarios.append(nuevo.model_dump())
        self.guardar_todos(usuarios)
        return nuevo

    def autenticar(self, correo: str, password: str) -> dict | None:
        usuario = self.buscar_por_correo(correo)
        if not usuario:
            return None

        clave_guardada = str(usuario.get("password_hash") or usuario.get("password") or "")
        if not self.verificar_password(password, clave_guardada):
            return None

        # Si estaba en texto plano, migrar automáticamente a hash seguro al iniciar sesión
        if not clave_guardada.startswith("pbkdf2_sha256$") and "password" in usuario:
            usuarios = self.listar_todos()
            for item in usuarios:
                if str(item.get("correo", "")).strip().lower() == correo.strip().lower():
                    item["password_hash"] = self.hashear_password(password)
                    item.pop("password", None)
            self.guardar_todos(usuarios)

        return usuario