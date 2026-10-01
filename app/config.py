from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ComicCraft - AI Comic Story Creator"

    debug: bool = True

    # Gemini
    gemini_api_key: str = ""
    gemini_flash_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-flash"

    # Hugging Face
    hf_api_key: str = ""
    hf_image_model: str = "black-forest-labs/FLUX.1-schnell"

    # Image provider
    image_provider: str = "huggingface"

    panel_count: int = 5

    image_width: int = 768
    image_height: int = 512

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()