from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import router


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered comic story creator "
        "using Gemini and Hugging Face."
    ),
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(
        directory="static"
    ),
    name="static",
)


app.include_router(router)


@app.get("/health")
def health():

    return {
        "status": "ok",
        "app": settings.app_name,
        "gemini_configured": bool(
            settings.gemini_api_key
        ),
        "image_provider": settings.image_provider,
        "hf_configured": bool(
            settings.hf_api_key
        ),
    }