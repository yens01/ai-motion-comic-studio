from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from src.models.project import Project
from src.utils.config import project_dir
from src.utils.images import save_png


def create_project_from_upload(file_name: str, raw_bytes: bytes, title: str | None = None) -> Project:
    stem = Path(file_name).stem or "comic"
    project = Project.create(title=title or stem)
    dest = project_dir(project.id)
    page_path = dest / "page.png"

    image = Image.open(BytesIO(raw_bytes)).convert("RGB")
    save_png(image, page_path)

    project.page_image_path = str(page_path)
    project.page_width = image.width
    project.page_height = image.height
    project.save(dest)
    return project


def load_page_image(project: Project) -> Image.Image:
    if not project.page_image_path:
        raise ValueError("專案尚未上傳漫畫頁面")
    return Image.open(project.page_image_path).convert("RGB")
