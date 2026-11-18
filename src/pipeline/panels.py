from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from src.models.project import Panel, PanelBox, Project
from src.utils.config import load_settings, project_dir
from src.utils.images import save_png


def _pil_to_cv(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def detect_panels(image: Image.Image, max_panels: int = 12) -> list[PanelBox]:
    """Heuristic comic panel detection via contours on a thresholded page."""
    bgr = _pil_to_cv(image)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    page_area = image.width * image.height
    min_area = page_area * 0.02
    max_area = page_area * 0.85

    boxes: list[PanelBox] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < min_area or area > max_area:
            continue
        aspect = w / max(h, 1)
        if aspect < 0.2 or aspect > 5.0:
            continue
        pad = 4
        boxes.append(
            PanelBox(
                left=max(0, x - pad),
                top=max(0, y - pad),
                right=min(image.width, x + w + pad),
                bottom=min(image.height, y + h + pad),
            )
        )

    boxes = _dedupe_boxes(boxes)
    boxes.sort(key=lambda b: (b.top // max(1, image.height // 20), b.left))

    if not boxes:
        # Fallback: single full-page panel
        boxes = [PanelBox(0, 0, image.width, image.height)]

    return boxes[:max_panels]


def _dedupe_boxes(boxes: list[PanelBox], iou_thresh: float = 0.55) -> list[PanelBox]:
    kept: list[PanelBox] = []
    for box in sorted(boxes, key=lambda b: b.width * b.height, reverse=True):
        if any(_iou(box, other) > iou_thresh for other in kept):
            continue
        kept.append(box)
    return kept


def _iou(a: PanelBox, b: PanelBox) -> float:
    x1 = max(a.left, b.left)
    y1 = max(a.top, b.top)
    x2 = min(a.right, b.right)
    y2 = min(a.bottom, b.bottom)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter == 0:
        return 0.0
    union = a.width * a.height + b.width * b.height - inter
    return inter / max(union, 1)


def apply_boxes_to_project(project: Project, image: Image.Image, boxes: list[PanelBox]) -> Project:
    settings = load_settings()
    default_style = settings["motion"]["default_style"]
    dest = project_dir(project.id)
    panels_dir = dest / "panels"

    # clear old panel images
    for old in panels_dir.glob("*.png"):
        old.unlink(missing_ok=True)

    panels: list[Panel] = []
    for idx, box in enumerate(boxes):
        clamped = box.clamp(image.width, image.height)
        panel = Panel.create(idx, clamped, motion_style=default_style)
        crop = image.crop(clamped.as_tuple())
        out = panels_dir / f"{panel.id}.png"
        save_png(crop, out)
        panel.image_path = str(out)
        panels.append(panel)

    project.panels = panels
    project.page_width = image.width
    project.page_height = image.height
    project.save(dest)
    return project


def update_panel_box(project: Project, image: Image.Image, panel_index: int, box: PanelBox) -> Project:
    if panel_index < 0 or panel_index >= len(project.panels):
        raise IndexError("panel_index out of range")
    clamped = box.clamp(image.width, image.height)
    panel = project.panels[panel_index]
    panel.box = clamped
    crop = image.crop(clamped.as_tuple())
    dest = project_dir(project.id) / "panels" / f"{panel.id}.png"
    save_png(crop, dest)
    panel.image_path = str(dest)
    project.save(project_dir(project.id))
    return project


def add_panel(project: Project, image: Image.Image, box: PanelBox | None = None) -> Project:
    if box is None:
        w, h = image.width, image.height
        box = PanelBox(w // 4, h // 4, w * 3 // 4, h * 3 // 4)
    boxes = [p.box for p in project.panels] + [box]
    return apply_boxes_to_project(project, image, boxes)


def remove_panel(project: Project, image: Image.Image, panel_index: int) -> Project:
    boxes = [p.box for i, p in enumerate(project.panels) if i != panel_index]
    if not boxes:
        boxes = [PanelBox(0, 0, image.width, image.height)]
    return apply_boxes_to_project(project, image, boxes)
