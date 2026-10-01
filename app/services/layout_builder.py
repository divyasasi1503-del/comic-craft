from typing import List

from app.schemas import ComicPanel


def build_comic_layout(
    panels: List[ComicPanel],
) -> List[dict]:

    layout = []

    for panel in panels:

        layout.append(
            {
                "panel_number": panel.panel_number,
                "title": panel.title,
                "image_path": panel.image_path,
                "scene_description": panel.scene_description,
                "caption": panel.caption,
                "narration": panel.narration,
                "dialogue": panel.dialogue,
                "image_prompt": panel.image_prompt,
            }
        )

    return layout