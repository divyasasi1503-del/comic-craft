from pathlib import Path
import re

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse,
)

from fastapi.templating import (
    Jinja2Templates,
)

from app.config import get_settings

from app.schemas import PromptRequest

from app.services.gemini_service import (
    GeminiService,
)

from app.services.image_generator import (
    ImageGenerator,
)

from app.services.layout_builder import (
    build_comic_layout,
)

from app.services.exporters import (
    save_pdf,
)


BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)

router = APIRouter()

settings = get_settings()

gemini = GeminiService(settings)

image_generator = ImageGenerator(
    settings,
    BASE_DIR / "static" / "panels",
)


def validate_form(
    story_prompt,
    character_name,
    setting,
    tone,
    art_style,
):

    values = [
        story_prompt,
        character_name,
        setting,
        tone,
        art_style,
    ]

    if any(
        not value or not value.strip()
        for value in values
    ):

        raise HTTPException(
            status_code=400,
            detail="All fields are required.",
        )


def generate_comic(
    request_data: PromptRequest,
):

    # Step 1:
    # Generate panel outline.
    outline = gemini.generate_outline(
        request_data.story_prompt,
        request_data.character_name,
        request_data.setting,
        request_data.tone,
        request_data.art_style,
        request_data.panel_count,
    )

    # Step 2:
    # Generate story and dialogue.
    panels = gemini.generate_story(
        outline,
        request_data.story_prompt,
        request_data.character_name,
        request_data.setting,
        request_data.tone,
    )

    # Step 3:
    # Generate image for every panel.
    for panel in panels:

        panel.image_path = (
            image_generator.generate(
                panel.image_prompt,
                panel.panel_number,
            )
        )

    # Step 4:
    # Build layout.
    layout = build_comic_layout(
        panels
    )

    # Step 5:
    # Export PDF.
    title = (
        f"{request_data.character_name}'s Comic"
    )

    pdf_url = save_pdf(
        layout,
        BASE_DIR / "static",
        title,
    )

    return {
        "title": title,
        "layout": layout,
        "pdf_url": pdf_url,
    }


@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "panel_count": settings.panel_count,
            "image_provider": settings.image_provider,
        },
    )


@router.post(
    "/generate",
    response_class=HTMLResponse,
)
def generate(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...),

    panel_count: int = Form(5),
):

    validate_form(
        story_prompt,
        character_name,
        setting,
        tone,
        art_style,
    )

    data = PromptRequest(
        story_prompt=story_prompt,
        character_name=character_name,
        setting=setting,
        tone=tone,
        art_style=art_style,
        panel_count=panel_count,
    )

    try:

        result = generate_comic(data)

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc),
                "panel_count": settings.panel_count,
                "image_provider": settings.image_provider,
            },
            status_code=500,
        )

    return templates.TemplateResponse(
        request=request,
        name="comic_preview.html",
        context=result,
    )


@router.post(
    "/generate-comic/json"
)
def generate_json(
    data: PromptRequest,
):

    try:

        return generate_comic(data)

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post(
    "/test-image"
)
def test_image(
    prompt: str = Form(...),
):

    if not prompt.strip():

        raise HTTPException(
            status_code=400,
            detail="Prompt is required.",
        )

    path = image_generator.generate(
        prompt,
        999,
    )

    return {
        "image_path": path
    }


@router.get(
    "/download/{filename}"
)
def download_pdf(
    filename: str,
):

    if not re.fullmatch(
        r"comic_\d{8}_\d{6}\.pdf",
        filename,
    ):

        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    file_path = (
        BASE_DIR
        / "static"
        / "exports"
        / filename
    )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
    )


@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
def export_success(
    request: Request,
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={},
    )