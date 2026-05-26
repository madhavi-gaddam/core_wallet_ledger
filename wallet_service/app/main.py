from fastapi import FastAPI

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.routes import users, wallets

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
)

register_exception_handlers(app)

app.include_router(users.router)
app.include_router(wallets.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

