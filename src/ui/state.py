from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.models.project import Project
from src.utils.config import project_dir


STEPS = [
    ("upload", "1. 上傳漫畫"),
    ("panels", "2. AI 分鏡切割"),
    ("script", "3. 台詞與劇本"),
    ("voice", "4. AI 角色配音"),
    ("motion", "5. 動態漫畫"),
    ("export", "6. 輸出影片"),
]


def init_session() -> None:
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "project" not in st.session_state:
        st.session_state.project = None
    if "project_id" not in st.session_state:
        st.session_state.project_id = None


def get_project() -> Project | None:
    return st.session_state.get("project")


def set_project(project: Project | None) -> None:
    st.session_state.project = project
    st.session_state.project_id = project.id if project else None


def persist_project(project: Project) -> Project:
    project.save(project_dir(project.id))
    set_project(project)
    return project


def reload_project(project_id: str) -> Project:
    project = Project.load(project_dir(project_id))
    set_project(project)
    return project


def list_saved_projects() -> list[tuple[str, str]]:
    from src.utils.config import projects_root

    items: list[tuple[str, str]] = []
    root = projects_root()
    for path in sorted(root.iterdir(), reverse=True):
        meta = path / "project.json"
        if not meta.exists():
            continue
        try:
            project = Project.load(path)
            items.append((project.id, project.title))
        except Exception:
            items.append((path.name, path.name))
    return items
