from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_rgb(path: str | Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def save_png(image: Image.Image, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")
    return path


def draw_boxes(image: Image.Image, boxes: list[tuple[int, int, int, int]], labels: list[str] | None = None) -> Image.Image:
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for i, (left, top, right, bottom) in enumerate(boxes):
        draw.rectangle((left, top, right, bottom), outline=(255, 64, 64), width=4)
        label = labels[i] if labels and i < len(labels) else str(i + 1)
        draw.rectangle((left, top, left + 36, top + 28), fill=(255, 64, 64))
        draw.text((left + 8, top + 4), label, fill=(255, 255, 255))
    return annotated


def make_end_card(
    width: int,
    height: int,
    title: str,
    subtitle: str,
    background=(18, 18, 24),
    accent=(255, 90, 95),
) -> Image.Image:
    img = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", size=max(36, width // 18))
        sub_font = ImageFont.truetype("arial.ttf", size=max(22, width // 32))
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    bar_h = max(8, height // 120)
    draw.rectangle((0, height // 2 - bar_h, width, height // 2 + bar_h), fill=accent)

    def center_text(text: str, y: int, font) -> None:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, y), text, fill=(245, 245, 245), font=font)

    center_text(title, height // 2 - max(80, height // 12), title_font)
    center_text(subtitle, height // 2 + max(40, height // 24), sub_font)
    return img


def image_to_bytes(image: Image.Image, fmt: str = "PNG") -> bytes:
    buf = BytesIO()
    image.save(buf, format=fmt)
    return buf.getvalue()
