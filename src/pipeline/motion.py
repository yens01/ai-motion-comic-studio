from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.models.project import Project
from src.utils.config import load_settings
from src.utils.images import make_end_card


def resolve_canvas(aspect_ratio: str) -> tuple[int, int]:
    settings = load_settings()
    key = "shorts" if aspect_ratio == "shorts" else "youtube"
    cfg = settings["video"][key]
    return int(cfg["width"]), int(cfg["height"])


def fit_cover(image: Image.Image, width: int, height: int) -> Image.Image:
    src_w, src_h = image.size
    scale = max(width / src_w, height / src_h)
    resized = image.resize((max(1, int(src_w * scale)), max(1, int(src_h * scale))), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def ken_burns_frame(
    image: Image.Image,
    width: int,
    height: int,
    progress: float,
    style: str = "zoom_in",
) -> Image.Image:
    """progress in [0, 1]."""
    p = max(0.0, min(1.0, progress))
    base = fit_cover(image, width, height)

    if style == "zoom_out":
        start, end = 1.18, 1.0
    elif style == "pan_left":
        start, end = 1.12, 1.12
    elif style == "pan_right":
        start, end = 1.12, 1.12
    else:  # zoom_in
        start, end = 1.0, 1.18

    scale = start + (end - start) * p
    zoom_w = max(width + 2, int(width * scale))
    zoom_h = max(height + 2, int(height * scale))
    zoomed = base.resize((zoom_w, zoom_h), Image.Resampling.LANCZOS)

    if style == "pan_left":
        max_x = zoom_w - width
        left = int(max_x * (1.0 - p))
        top = (zoom_h - height) // 2
    elif style == "pan_right":
        max_x = zoom_w - width
        left = int(max_x * p)
        top = (zoom_h - height) // 2
    else:
        left = (zoom_w - width) // 2
        top = (zoom_h - height) // 2

    return zoomed.crop((left, top, left + width, top + height))


def panel_duration(project: Project, panel_index: int) -> float:
    settings = load_settings()
    default = float(settings["video"]["default_panel_seconds"])
    panel = project.panels[panel_index]
    if panel.dialogue and panel.dialogue.duration_hint > 0:
        return float(panel.dialogue.duration_hint)
    return default


def build_timeline(project: Project) -> list[dict]:
    """Return timeline entries for UI preview and export."""
    settings = load_settings()
    end_secs = float(settings["video"]["end_card_seconds"])
    cursor = 0.0
    entries: list[dict] = []

    for i, panel in enumerate(project.panels):
        dur = panel_duration(project, i)
        text = panel.dialogue.text if panel.dialogue else ""
        speaker = panel.dialogue.speaker if panel.dialogue else ""
        entries.append(
            {
                "kind": "panel",
                "panel_id": panel.id,
                "index": i,
                "start": cursor,
                "end": cursor + dur,
                "duration": dur,
                "motion_style": panel.motion_style,
                "speaker": speaker,
                "text": text,
                "image_path": panel.image_path,
                "audio_path": panel.dialogue.audio_path if panel.dialogue else None,
            }
        )
        cursor += dur

    width, height = resolve_canvas(project.aspect_ratio)
    end_card = make_end_card(width, height, project.next_episode_title, project.next_episode_subtitle)
    entries.append(
        {
            "kind": "end_card",
            "panel_id": "end_card",
            "index": len(project.panels),
            "start": cursor,
            "end": cursor + end_secs,
            "duration": end_secs,
            "motion_style": "none",
            "speaker": "",
            "text": f"{project.next_episode_title} — {project.next_episode_subtitle}",
            "image": end_card,
            "audio_path": None,
        }
    )
    return entries


def update_motion_styles(project: Project, styles: dict[str, str]) -> Project:
    from src.utils.config import project_dir

    for panel in project.panels:
        if panel.id in styles:
            panel.motion_style = styles[panel.id]
    project.save(project_dir(project.id))
    return project
