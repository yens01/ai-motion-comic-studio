from __future__ import annotations

import asyncio
from pathlib import Path

from src.models.project import Project
from src.utils.config import load_settings, project_dir


async def _synthesize(text: str, voice: str, out_path: Path) -> Path:
    import edge_tts

    out_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(out_path))
    return out_path


def synthesize_line(text: str, voice: str, out_path: Path) -> Path:
    cleaned = (text or "").strip()
    if not cleaned:
        # write a tiny silent-ish placeholder by speaking a short pause cue
        cleaned = "。"
    return asyncio.run(_synthesize(cleaned, voice, out_path))


def generate_project_audio(project: Project, force: bool = False) -> Project:
    settings = load_settings()
    default_voice = settings["tts"]["default_voice"]
    audio_dir = project_dir(project.id) / "audio"

    for panel in project.panels:
        dialogue = panel.dialogue
        if dialogue is None:
            continue
        out = audio_dir / f"{panel.id}.mp3"
        if out.exists() and dialogue.audio_path and not force:
            continue
        voice = dialogue.voice_id or default_voice
        synthesize_line(dialogue.text, voice, out)
        dialogue.audio_path = str(out)

    project.save(project_dir(project.id))
    return project


def generate_panel_audio(project: Project, panel_id: str) -> Project:
    settings = load_settings()
    default_voice = settings["tts"]["default_voice"]
    audio_dir = project_dir(project.id) / "audio"

    for panel in project.panels:
        if panel.id != panel_id or panel.dialogue is None:
            continue
        out = audio_dir / f"{panel.id}.mp3"
        voice = panel.dialogue.voice_id or default_voice
        synthesize_line(panel.dialogue.text, voice, out)
        panel.dialogue.audio_path = str(out)
        break

    project.save(project_dir(project.id))
    return project
