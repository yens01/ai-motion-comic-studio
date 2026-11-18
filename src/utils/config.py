from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = ROOT / "config" / "settings.yaml"


@lru_cache(maxsize=1)
def load_settings() -> dict[str, Any]:
    with SETTINGS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def projects_root() -> Path:
    settings = load_settings()
    path = ROOT / settings["paths"]["projects_dir"]
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_dir(project_id: str) -> Path:
    path = projects_root() / project_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "panels").mkdir(exist_ok=True)
    (path / "audio").mkdir(exist_ok=True)
    (path / "output").mkdir(exist_ok=True)
    return path
