from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json
import uuid
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PanelBox:
    left: int
    top: int
    right: int
    bottom: int

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)

    def clamp(self, width: int, height: int) -> "PanelBox":
        left = max(0, min(self.left, width - 1))
        top = max(0, min(self.top, height - 1))
        right = max(left + 1, min(self.right, width))
        bottom = max(top + 1, min(self.bottom, height))
        return PanelBox(left, top, right, bottom)

    @property
    def width(self) -> int:
        return max(1, self.right - self.left)

    @property
    def height(self) -> int:
        return max(1, self.bottom - self.top)


@dataclass
class DialogueLine:
    panel_id: str
    speaker: str = "旁白"
    text: str = ""
    voice_id: str = "zh-TW-HsiaoChenNeural"
    duration_hint: float = 3.0
    audio_path: str | None = None
    sfx_note: str = ""


@dataclass
class Panel:
    id: str
    index: int
    box: PanelBox
    image_path: str | None = None
    motion_style: str = "zoom_in"
    dialogue: DialogueLine | None = None

    @staticmethod
    def create(index: int, box: PanelBox, motion_style: str = "zoom_in") -> "Panel":
        panel_id = f"panel_{index + 1:02d}"
        return Panel(
            id=panel_id,
            index=index,
            box=box,
            motion_style=motion_style,
            dialogue=DialogueLine(panel_id=panel_id),
        )


@dataclass
class Project:
    id: str
    title: str
    created_at: str
    updated_at: str
    page_image_path: str | None = None
    page_width: int = 0
    page_height: int = 0
    panels: list[Panel] = field(default_factory=list)
    aspect_ratio: str = "shorts"  # shorts | youtube
    next_episode_title: str = "下一集推薦"
    next_episode_subtitle: str = "點擊追蹤，繼續觀看"
    output_paths: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def create(title: str = "未命名專案") -> "Project":
        now = _now_iso()
        return Project(
            id=uuid.uuid4().hex[:12],
            title=title,
            created_at=now,
            updated_at=now,
        )

    def touch(self) -> None:
        self.updated_at = _now_iso()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Project":
        panels: list[Panel] = []
        for raw in data.get("panels", []):
            box = PanelBox(**raw["box"])
            dialogue = None
            if raw.get("dialogue"):
                dialogue = DialogueLine(**raw["dialogue"])
            panels.append(
                Panel(
                    id=raw["id"],
                    index=raw["index"],
                    box=box,
                    image_path=raw.get("image_path"),
                    motion_style=raw.get("motion_style", "zoom_in"),
                    dialogue=dialogue,
                )
            )
        return Project(
            id=data["id"],
            title=data.get("title", "未命名專案"),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            page_image_path=data.get("page_image_path"),
            page_width=data.get("page_width", 0),
            page_height=data.get("page_height", 0),
            panels=panels,
            aspect_ratio=data.get("aspect_ratio", "shorts"),
            next_episode_title=data.get("next_episode_title", "下一集推薦"),
            next_episode_subtitle=data.get("next_episode_subtitle", "點擊追蹤，繼續觀看"),
            output_paths=data.get("output_paths", {}),
        )

    def save(self, project_dir: Path) -> Path:
        project_dir.mkdir(parents=True, exist_ok=True)
        self.touch()
        path = project_dir / "project.json"
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @staticmethod
    def load(project_dir: Path) -> "Project":
        path = project_dir / "project.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return Project.from_dict(data)
