from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from src.models.project import Project
from src.pipeline.motion import build_timeline, ken_burns_frame, resolve_canvas
from src.utils.config import load_settings, project_dir
from src.utils.images import make_end_card, save_png


def _ffprobe_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except FileNotFoundError:
        return None
    return None


def seconds_to_srt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(timeline: list[dict], path: Path) -> Path:
    lines: list[str] = []
    idx = 1
    for entry in timeline:
        text = (entry.get("text") or "").strip()
        if not text or entry.get("kind") == "end_card":
            # still include end card as soft prompt
            if entry.get("kind") != "end_card":
                continue
        speaker = (entry.get("speaker") or "").strip()
        body = f"{speaker}: {text}" if speaker and entry.get("kind") != "end_card" else text
        if not body.strip():
            continue
        lines.append(str(idx))
        lines.append(f"{seconds_to_srt_ts(entry['start'])} --> {seconds_to_srt_ts(entry['end'])}")
        lines.append(body)
        lines.append("")
        idx += 1
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _render_frames(project: Project, timeline: list[dict], frames_dir: Path, fps: int) -> list[Path]:
    width, height = resolve_canvas(project.aspect_ratio)
    frame_paths: list[Path] = []
    frame_i = 0

    for entry in timeline:
        n_frames = max(1, int(round(entry["duration"] * fps)))
        if entry["kind"] == "end_card":
            image = entry.get("image") or make_end_card(
                width, height, project.next_episode_title, project.next_episode_subtitle
            )
            for _ in range(n_frames):
                out = frames_dir / f"frame_{frame_i:06d}.png"
                save_png(image, out)
                frame_paths.append(out)
                frame_i += 1
            continue

        src = Image.open(entry["image_path"]).convert("RGB")
        style = entry.get("motion_style") or "zoom_in"
        for f in range(n_frames):
            progress = 0.0 if n_frames == 1 else f / (n_frames - 1)
            frame = ken_burns_frame(src, width, height, progress, style)
            out = frames_dir / f"frame_{frame_i:06d}.png"
            save_png(frame, out)
            frame_paths.append(out)
            frame_i += 1
    return frame_paths


def _build_audio_track(timeline: list[dict], work_dir: Path, total_duration: float) -> Path | None:
    """Concatenate per-panel audio with padding using ffmpeg; return mixed wav/mp3 path."""
    segments: list[Path] = []
    for i, entry in enumerate(timeline):
        if entry["kind"] != "panel":
            continue
        audio_path = entry.get("audio_path")
        dur = float(entry["duration"])
        seg = work_dir / f"seg_{i:02d}.mp3"
        if audio_path and Path(audio_path).exists():
            # trim/pad to panel duration
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(audio_path),
                    "-t",
                    f"{dur:.3f}",
                    "-af",
                    f"apad=whole_dur={dur:.3f}",
                    "-ar",
                    "44100",
                    "-ac",
                    "2",
                    str(seg),
                ],
                capture_output=True,
                check=False,
            )
        else:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=r=44100:cl=stereo",
                    "-t",
                    f"{dur:.3f}",
                    str(seg),
                ],
                capture_output=True,
                check=False,
            )
        if seg.exists():
            segments.append(seg)

    # end card silence
    end_entries = [e for e in timeline if e["kind"] == "end_card"]
    if end_entries:
        end_dur = float(end_entries[0]["duration"])
        end_seg = work_dir / "seg_end.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=stereo",
                "-t",
                f"{end_dur:.3f}",
                str(end_seg),
            ],
            capture_output=True,
            check=False,
        )
        if end_seg.exists():
            segments.append(end_seg)

    if not segments:
        return None

    list_file = work_dir / "audio_concat.txt"
    list_file.write_text("\n".join(f"file '{p.as_posix()}'" for p in segments), encoding="utf-8")
    mixed = work_dir / "mixed_audio.mp3"
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(mixed)],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not mixed.exists():
        return None
    return mixed


def export_project(project: Project, aspect_ratio: str | None = None) -> dict[str, str]:
    settings = load_settings()
    if aspect_ratio:
        project.aspect_ratio = aspect_ratio

    fps = int(settings["video"]["fps"])
    dest = project_dir(project.id)
    out_dir = dest / "output"
    out_dir.mkdir(exist_ok=True)

    # Sync duration hints from audio when available
    for panel in project.panels:
        if panel.dialogue and panel.dialogue.audio_path:
            probed = _ffprobe_duration(Path(panel.dialogue.audio_path))
            if probed and probed > 0.4:
                panel.dialogue.duration_hint = max(float(panel.dialogue.duration_hint), probed + 0.15)

    timeline = build_timeline(project)
    total_duration = timeline[-1]["end"] if timeline else 0.0

    srt_path = out_dir / f"{project.id}_{project.aspect_ratio}.srt"
    write_srt(timeline, srt_path)

    width, height = resolve_canvas(project.aspect_ratio)
    end_card = make_end_card(width, height, project.next_episode_title, project.next_episode_subtitle)
    end_card_path = out_dir / f"{project.id}_end_card.png"
    save_png(end_card, end_card_path)

    mp4_path = out_dir / f"{project.id}_{project.aspect_ratio}.mp4"

    with tempfile.TemporaryDirectory(prefix="mcs_export_") as tmp:
        tmp_path = Path(tmp)
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()
        _render_frames(project, timeline, frames_dir, fps)
        audio = _build_audio_track(timeline, tmp_path, total_duration)

        frame_pattern = str(frames_dir / "frame_%06d.png")
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            frame_pattern,
        ]
        if audio:
            cmd.extend(["-i", str(audio)])
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
            ]
        )
        if audio:
            cmd.extend(["-c:a", "aac", "-shortest"])
        cmd.append(str(mp4_path))

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not mp4_path.exists():
            raise RuntimeError(
                "FFmpeg 匯出失敗。請確認已安裝 ffmpeg 並加入 PATH。\n"
                + (result.stderr[-1200:] if result.stderr else "")
            )

    outputs = {
        "mp4": str(mp4_path),
        "srt": str(srt_path),
        "end_card": str(end_card_path),
    }
    project.output_paths = outputs
    project.save(dest)
    return outputs
