import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.controllers import api_router, auth_router, pages_router

logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="GameFinder API & Web",
    description="Buscador y gestor inteligente de videojuegos con arquitectura MVC, SOLID y Patrones de Diseño.",
    version="2.0.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("FLASK_SECRET_KEY", "gamefinder-clave-local"),
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(api_router)