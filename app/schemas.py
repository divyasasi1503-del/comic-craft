from typing import List

from pydantic import BaseModel, Field, field_validator


class PromptRequest(BaseModel):
    story_prompt: str = Field(
        min_length=5,
        max_length=2000
    )

    character_name: str = Field(
        min_length=1,
        max_length=100
    )

    setting: str = Field(
        min_length=1,
        max_length=120
    )

    tone: str = Field(
        min_length=1,
        max_length=60
    )

    art_style: str = Field(
        min_length=1,
        max_length=80
    )

    panel_count: int = Field(
        default=5,
        ge=3,
        le=8
    )

    @field_validator("*", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value


class PanelOutline(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str


class ComicOutline(BaseModel):
    panels: List[PanelOutline]


class ComicPanel(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str

    caption: str = ""
    narration: str = ""
    dialogue: str = ""

    image_path: str = ""


class ComicResponse(BaseModel):
    title: str
    panels: List[ComicPanel]
    pdf_url: str