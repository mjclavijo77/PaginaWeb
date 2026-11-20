from backend.controllers.api_controller import router as api_router
from backend.controllers.auth_controller import router as auth_router
from backend.controllers.pages_controller import router as pages_router

__all__ = ["api_router", "auth_router", "pages_router"]