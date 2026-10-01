import json
import time
from typing import List, Callable, Any

from google import genai
from google.genai import types

from app.config import Settings
from app.schemas import (
    ComicOutline,
    PanelOutline,
    ComicPanel,
)


class GeminiService:
    """
    Handles Gemini text-generation operations.

    Includes automatic retry handling for temporary
    Gemini errors.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

        if settings.gemini_api_key:
            self.client = genai.Client(
                api_key=settings.gemini_api_key
            )
        else:
            self.client = None

    def _check_client(self):
        if self.client is None:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. "
                "Add your Gemini API key to the .env file."
            )

    def _is_retryable_error(self, error: Exception) -> bool:
        error_text = str(error).upper()

        retryable_errors = [
            "503",
            "UNAVAILABLE",
            "SERVICE UNAVAILABLE",
            "RESOURCE EXHAUSTED",
            "429",
            "TOO MANY REQUESTS",
            "INTERNAL",
            "500",
            "502",
            "504",
        ]

        return any(
            error_code in error_text
            for error_code in retryable_errors
        )

    def _generate_with_retry(
        self,
        generate_function: Callable[[], Any],
        operation_name: str,
        max_retries: int = 4,
    ):
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                print(
                    f"[Gemini] {operation_name}: "
                    f"attempt {attempt}/{max_retries}"
                )

                response = generate_function()

                print(
                    f"[Gemini] {operation_name}: "
                    "generation successful"
                )

                return response

            except Exception as error:
                last_error = error

                print(
                    f"[Gemini] {operation_name} failed: "
                    f"{error}"
                )

                if not self._is_retryable_error(error):
                    raise

                if attempt >= max_retries:
                    raise RuntimeError(
                        f"Gemini actual error: {error}"
                    ) from error

                delay = 5 * (2 ** (attempt - 1))

                print(
                    f"[Gemini] Temporary error detected. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

        raise RuntimeError(
            "Gemini generation failed."
        ) from last_error

    def generate_outline(
        self,
        story_prompt: str,
        character_name: str,
        setting: str,
        tone: str,
        art_style: str,
        panel_count: int,
    ) -> ComicOutline:

        self._check_client()

        prompt = f"""
Create a cohesive {panel_count}-panel comic outline.

Story idea:
{story_prompt}

Main character:
{character_name}

Setting:
{setting}

Tone:
{tone}

Art style:
{art_style}

Requirements:

1. Create exactly {panel_count} panels.
2. Maintain character consistency.
3. Each panel must continue naturally from the previous panel.
4. Provide a clear scene description.
5. Provide an image generation prompt for each panel.
6. Return structured JSON matching the requested schema.
"""

        def request():
            return self.client.models.generate_content(
                model=self.settings.gemini_flash_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ComicOutline,
                    temperature=0.8,
                ),
            )

        response = self._generate_with_retry(
            generate_function=request,
            operation_name="comic outline",
        )

        if getattr(response, "parsed", None):
            outline = response.parsed

        else:
            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response "
                    "while generating the comic outline."
                )

            outline = ComicOutline.model_validate_json(
                response.text
            )

        if len(outline.panels) != panel_count:

            panels = outline.panels[:panel_count]

            while len(panels) < panel_count:

                number = len(panels) + 1

                panels.append(
                    PanelOutline(
                        panel_number=number,
                        title=f"Panel {number}",
                        scene_description=(
                            "A natural continuation "
                            "of the story."
                        ),
                        image_prompt=(
                            f"{art_style} comic panel, "
                            f"{character_name} in {setting}, "
                            "cinematic composition, "
                            "consistent character design."
                        ),
                    )
                )

            outline.panels = panels

        return outline

    def generate_story(
        self,
        outline: ComicOutline,
        story_prompt: str,
        character_name: str,
        setting: str,
        tone: str,
    ) -> List[ComicPanel]:

        self._check_client()

        outline_json = json.dumps(
            [
                panel.model_dump()
                for panel in outline.panels
            ],
            ensure_ascii=False,
            indent=2,
        )

        prompt = f"""
Expand this comic outline into a complete
panel-by-panel comic script.

Original story idea:
{story_prompt}

Main character:
{character_name}

Setting:
{setting}

Tone:
{tone}

Comic outline:
{outline_json}

Requirements:

1. Keep the same story continuity.
2. Keep the character consistent.
3. Create dialogue where appropriate.
4. Create narration where appropriate.
5. Create captions where appropriate.
6. Return one ComicPanel for every panel.
7. Return structured JSON matching the requested schema.
"""

        def request():
            return self.client.models.generate_content(
                model=self.settings.gemini_pro_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[ComicPanel],
                    temperature=0.85,
                ),
            )

        response = self._generate_with_retry(
            generate_function=request,
            operation_name="comic story",
        )

        if getattr(response, "parsed", None):
            panels = response.parsed

        else:
            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response "
                    "while generating the comic story."
                )

            raw_data = json.loads(
                response.text
            )

            panels = [
                ComicPanel.model_validate(item)
                for item in raw_data
            ]

        generated = {
            panel.panel_number: panel
            for panel in panels
        }

        result = []

        for original in outline.panels:

            panel = generated.get(
                original.panel_number
            )

            if panel is None:

                panel = ComicPanel(
                    **original.model_dump(),
                    caption="",
                    narration=original.scene_description,
                    dialogue="",
                )

            result.append(panel)

        return result