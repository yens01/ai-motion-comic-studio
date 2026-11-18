from __future__ import annotations

from functools import lru_cache

from PIL import Image

from src.models.project import DialogueLine, Project
from src.utils.config import load_settings, project_dir


@lru_cache(maxsize=1)
def _reader():
    import easyocr

    langs = load_settings()["ocr"]["languages"]
    # EasyOCR uses 'ch_tra' for traditional Chinese
    return easyocr.Reader(langs, gpu=False)


def run_ocr_on_image(image: Image.Image) -> str:
    import numpy as np

    reader = _reader()
    arr = np.array(image.convert("RGB"))
    results = reader.readtext(arr, detail=0, paragraph=True)
    if isinstance(results, list):
        return "\n".join(str(x).strip() for x in results if str(x).strip())
    return str(results).strip()


def run_ocr_for_project(project: Project, overwrite_empty_only: bool = True) -> Project:
    settings = load_settings()
    default_voice = settings["tts"]["default_voice"]
    default_duration = float(settings["video"]["default_panel_seconds"])

    for panel in project.panels:
        if panel.dialogue is None:
            panel.dialogue = DialogueLine(panel_id=panel.id, voice_id=default_voice, duration_hint=default_duration)
        if overwrite_empty_only and panel.dialogue.text.strip():
            continue
        if not panel.image_path:
            continue
        image = Image.open(panel.image_path).convert("RGB")
        text = run_ocr_on_image(image)
        panel.dialogue.text = text
        panel.dialogue.panel_id = panel.id
        if not panel.dialogue.voice_id:
            panel.dialogue.voice_id = default_voice
        if panel.dialogue.duration_hint <= 0:
            panel.dialogue.duration_hint = default_duration

    project.save(project_dir(project.id))
    return project


def update_dialogue(
    project: Project,
    panel_id: str,
    *,
    speaker: str | None = None,
    text: str | None = None,
    voice_id: str | None = None,
    duration_hint: float | None = None,
    sfx_note: str | None = None,
) -> Project:
    for panel in project.panels:
        if panel.id != panel_id:
            continue
        if panel.dialogue is None:
            panel.dialogue = DialogueLine(panel_id=panel.id)
        if speaker is not None:
            panel.dialogue.speaker = speaker
        if text is not None:
            panel.dialogue.text = text
        if voice_id is not None:
            panel.dialogue.voice_id = voice_id
        if duration_hint is not None:
            panel.dialogue.duration_hint = float(duration_hint)
        if sfx_note is not None:
            panel.dialogue.sfx_note = sfx_note
        break
    project.save(project_dir(project.id))
    return project
