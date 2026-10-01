from pathlib import Path
from datetime import datetime
import unicodedata
import re

from fpdf import FPDF


def pdf_safe(text: str) -> str:
    """
    Convert text to a safe representation for FPDF.
    """

    if text is None:
        return ""

    text = str(text)

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    replacements = {
        "—": "-",
        "–": "-",
        "−": "-",
        "“": '"',
        "”": '"',
        "„": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "\u00a0": " ",
        "\u200b": "",
        "\ufeff": "",
        "\t": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove unsupported control characters.
    cleaned = []

    for char in text:

        code = ord(char)

        if char in "\n\r":
            cleaned.append(char)

        elif code >= 32:
            cleaned.append(char)

    text = "".join(cleaned)

    # FPDF built-in Helvetica uses latin-1.
    text = (
        text
        .encode(
            "latin-1",
            "replace",
        )
        .decode("latin-1")
    )

    return text


def break_long_words(
    text: str,
    max_length: int = 25,
) -> str:
    """
    Break extremely long words/tokens.

    This prevents:
        Not enough horizontal space to render
        a single character
    """

    text = pdf_safe(text)

    if not text:
        return ""

    result = []

    for line in text.splitlines():

        if not line.strip():
            result.append("")
            continue

        words = line.split()

        new_words = []

        for word in words:

            if len(word) <= max_length:

                new_words.append(word)
                continue

            # Break long tokens into smaller pieces.
            chunks = []

            for i in range(
                0,
                len(word),
                max_length,
            ):

                chunk = word[
                    i:i + max_length
                ]

                chunks.append(chunk)

            new_words.extend(chunks)

        result.append(
            " ".join(new_words)
        )

    return "\n".join(result)


def write_text(
    pdf: FPDF,
    text: str,
    line_height: float = 7,
):
    """
    Safely write text to the current PDF page.
    """

    text = break_long_words(text)

    if not text:
        return

    # Explicitly reset x position.
    # This is important when multi_cell()
    # follows an image or previous block.
    pdf.set_x(
        pdf.l_margin
    )

    try:

        pdf.multi_cell(
            w=pdf.epw,
            h=line_height,
            text=text,
            border=0,
            align="L",
        )

    except Exception:

        # Last-resort fallback:
        # write one short line at a time.
        for line in text.splitlines():

            if not line:
                pdf.ln(line_height)
                continue

            safe_line = break_long_words(
                line,
                max_length=15,
            )

            pdf.set_x(
                pdf.l_margin
            )

            pdf.multi_cell(
                w=pdf.epw,
                h=line_height,
                text=safe_line,
                border=0,
                align="L",
            )


def save_pdf(
    layout: list[dict],
    static_dir: Path,
    title: str = "ComicCraft Comic",
) -> str:

    exports_dir = (
        static_dir / "exports"
    )

    exports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"comic_{timestamp}.pdf"
    )

    output_path = (
        exports_dir / filename
    )

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4",
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )

    pdf.set_margins(
        left=15,
        top=15,
        right=15,
    )

    pdf.set_title(
        pdf_safe(title)
    )

    for panel_index, panel in enumerate(
        layout,
        start=1,
    ):

        pdf.add_page()

        # ---------------------------------
        # PANEL TITLE
        # ---------------------------------

        panel_number = panel.get(
            "panel_number",
            panel_index,
        )

        panel_title = panel.get(
            "title",
            f"Panel {panel_number}",
        )

        pdf.set_font(
            "Helvetica",
            "B",
            18,
        )

        write_text(
            pdf,
            (
                f"Panel {panel_number}: "
                f"{panel_title}"
            ),
            10,
        )

        # ---------------------------------
        # PANEL IMAGE
        # ---------------------------------

        image_path_value = panel.get(
            "image_path",
            "",
        )

        image_path = None

        if image_path_value:

            image_path = (
                static_dir.parent
                / str(
                    image_path_value
                ).lstrip("/")
            )

        if (
            image_path is not None
            and image_path.exists()
        ):

            try:

                pdf.image(
                    str(image_path),
                    x=15,
                    y=38,
                    w=180,
                    h=120,
                )

                pdf.set_y(165)

            except Exception:

                pdf.set_y(45)

        else:

            pdf.set_y(45)

        # ---------------------------------
        # SCENE DESCRIPTION
        # ---------------------------------

        pdf.set_font(
            "Helvetica",
            "I",
            11,
        )

        write_text(
            pdf,
            panel.get(
                "scene_description",
                "",
            ),
            7,
        )

        pdf.ln(3)

        # ---------------------------------
        # CAPTION
        # ---------------------------------

        pdf.set_font(
            "Helvetica",
            "B",
            11,
        )

        write_text(
            pdf,
            "Caption",
            7,
        )

        pdf.set_font(
            "Helvetica",
            "",
            11,
        )

        write_text(
            pdf,
            panel.get(
                "caption",
                "",
            ),
            7,
        )

        pdf.ln(2)

        # ---------------------------------
        # NARRATION
        # ---------------------------------

        pdf.set_font(
            "Helvetica",
            "B",
            11,
        )

        write_text(
            pdf,
            "Narration",
            7,
        )

        pdf.set_font(
            "Helvetica",
            "",
            11,
        )

        write_text(
            pdf,
            panel.get(
                "narration",
                "",
            ),
            7,
        )

        # ---------------------------------
        # DIALOGUE
        # ---------------------------------

        dialogue = panel.get(
            "dialogue",
            "",
        )

        if dialogue:

            pdf.ln(2)

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            write_text(
                pdf,
                "Dialogue",
                7,
            )

            pdf.set_font(
                "Helvetica",
                "",
                11,
            )

            write_text(
                pdf,
                dialogue,
                7,
            )

    # -------------------------------------
    # SAVE PDF
    # -------------------------------------

    pdf.output(
        str(output_path)
    )

    return (
        f"/static/exports/{filename}"
    )


__all__ = [
    "save_pdf",
    "pdf_safe",
]
