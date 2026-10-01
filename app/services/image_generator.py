from pathlib import Path
import time

from PIL import Image
from huggingface_hub import InferenceClient

from app.config import Settings


class ImageGenerator:
    """
    Generates comic panel images using Hugging Face.
    """

    def __init__(
        self,
        settings: Settings,
        output_dir: Path,
    ):
        self.settings = settings
        self.output_dir = output_dir

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def generate(
        self,
        prompt: str,
        panel_number: int,
    ) -> str:

        filename = f"panel_{panel_number}.png"

        target = self.output_dir / filename

        # -----------------------------------------
        # CHECK API KEY
        # -----------------------------------------

        if not self.settings.hf_api_key:
            raise RuntimeError(
                "Hugging Face API key is missing. "
                "Add HF_API_KEY to your .env file."
            )

        # -----------------------------------------
        # MODEL
        # -----------------------------------------

        model = (
            self.settings.hf_image_model
            or "black-forest-labs/FLUX.1-schnell"
        )

        print()
        print("=" * 60)
        print("COMICCRAFT IMAGE GENERATION")
        print("=" * 60)
        print(f"Panel : {panel_number}")
        print(f"Model : {model}")
        print(f"Prompt: {prompt}")
        print("=" * 60)

        # -----------------------------------------
        # HUGGING FACE CLIENT
        # -----------------------------------------

        client = InferenceClient(
            provider="auto",
            api_key=self.settings.hf_api_key,
        )

        last_error = None

        # -----------------------------------------
        # RETRY 3 TIMES
        # -----------------------------------------

        for attempt in range(1, 4):

            try:

                print(
                    f"[HF] Generation attempt "
                    f"{attempt}/3..."
                )

                # ---------------------------------
                # GENERATE IMAGE
                # ---------------------------------

                image = client.text_to_image(
                    prompt=prompt,
                    model=model,
                    width=self.settings.image_width,
                    height=self.settings.image_height,
                )

                # ---------------------------------
                # VALIDATE IMAGE
                # ---------------------------------

                if image is None:
                    raise RuntimeError(
                        "Hugging Face returned no image."
                    )

                if not isinstance(
                    image,
                    Image.Image,
                ):
                    raise RuntimeError(
                        "Hugging Face returned an "
                        "unexpected response instead "
                        "of a PIL image."
                    )

                # ---------------------------------
                # SAVE PNG
                # ---------------------------------

                image.save(
                    target,
                    format="PNG",
                )

                print(
                    f"[HF] SUCCESS: {target}"
                )

                print(
                    f"[HF] Image size: "
                    f"{image.size}"
                )

                print("=" * 60)
                print()

                return (
                    f"/static/panels/{filename}"
                )

            except Exception as error:

                last_error = error

                print()
                print(
                    f"[HF] Attempt {attempt} failed:"
                )
                print(
                    f"[HF] Error type: "
                    f"{type(error).__name__}"
                )
                print(
                    f"[HF] Error message: "
                    f"{str(error)}"
                )
                print(
                    f"[HF] Full error: "
                    f"{repr(error)}"
                )

                # ---------------------------------
                # RETRY
                # ---------------------------------

                if attempt < 3:

                    delay = 5 * attempt

                    print(
                        f"[HF] Retrying in "
                        f"{delay} seconds..."
                    )

                    time.sleep(delay)

        # -----------------------------------------
        # FINAL ERROR
        # -----------------------------------------

        raise RuntimeError(
            "Hugging Face image generation failed "
            f"after 3 attempts. "
            f"Model: {model}. "
            f"Last error: {last_error}"
        ) from last_error