from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.controllers.dependencies import (
    agregar_flash,
    get_user_repo,
    obtener_flashes,
    templates,
)
from backend.models.schemas import UsuarioCreate
from backend.repositories import UserRepository

router = APIRouter(tags=["Autenticación (Vistas)"])


@router.get("/registro", response_class=HTMLResponse, name="registro")
def vista_registro(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="registro.html",
        context={
            "error": None,
            "mensajes": obtener_flashes(request),
            "form_data": {},
        },
    )


@router.post("/registro", response_class=HTMLResponse)
def procesar_registro(
    request: Request,
    correo: str = Form(""),
    usuario: str = Form(""),
    password: str = Form(""),
    confirm_password: str = Form("", alias="confirm-password"),
    user_repo: UserRepository = Depends(get_user_repo),
):
    correo_limpio = correo.strip().lower()
    usuario_limpio = usuario.strip()
    form_data = {"correo": correo_limpio, "usuario": usuario_limpio}

    if not correo_limpio or not usuario_limpio or not password:
        return templates.TemplateResponse(
            request=request,
            name="registro.html",
            context={
                "error": "Debes completar todos los campos.",
                "mensajes": [],
                "form_data": form_data,
            },
        )

    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="registro.html",
            context={
                "error": "Las contraseñas no coinciden.",
                "mensajes": [],
                "form_data": form_data,
            },
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="registro.html",
            context={
                "error": "La contraseña debe tener al menos 6 caracteres.",
                "mensajes": [],
                "form_data": form_data,
            },
        )

    nuevo = UsuarioCreate(correo=correo_limpio, usuario=usuario_limpio, password=password)
    creado = user_repo.crear_usuario(nuevo)

    if not creado:
        return templates.TemplateResponse(
            request=request,
            name="registro.html",
            context={
                "error": "Ese correo ya está registrado.",
                "mensajes": [],
                "form_data": form_data,
            },
        )

    agregar_flash(request, "Cuenta creada correctamente. Ya puedes iniciar sesión.")
    return RedirectResponse(url=request.url_for("login"), status_code=303)


@router.get("/login", response_class=HTMLResponse, name="login")
def vista_login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
            "mensajes": obtener_flashes(request),
            "form_data": {},
        },
    )


@router.post("/login", response_class=HTMLResponse)
def procesar_login(
    request: Request,
    correo: str = Form(""),
    password: str = Form(""),
    user_repo: UserRepository = Depends(get_user_repo),
):
    correo_limpio = correo.strip().lower()
    usuario = user_repo.autenticar(correo_limpio, password)

    if usuario:
        request.session.clear()
        request.session["correo"] = usuario["correo"]
        request.session["usuario"] = usuario.get("usuario", correo_limpio)
        return RedirectResponse(url=request.url_for("inicio"), status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": "Correo o contraseña incorrectos.",
            "mensajes": [],
            "form_data": {"correo": correo_limpio},
        },
    )


@router.get("/logout", name="logout")
def logout(request: Request):
    request.session.clear()
    agregar_flash(request, "Has cerrado sesión.")
    return RedirectResponse(url=request.url_for("inicio"), status_code=303)