from PIL import Image, ImageDraw

from src.pipeline.panels import detect_panels


def test_detect_panels_finds_rectangles():
    image = Image.new("RGB", (600, 800), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    # two panel-like dark bordered regions
    draw.rectangle((40, 40, 280, 360), outline=(0, 0, 0), width=8, fill=(245, 245, 245))
    draw.rectangle((320, 40, 560, 360), outline=(0, 0, 0), width=8, fill=(245, 245, 245))
    draw.rectangle((40, 400, 560, 760), outline=(0, 0, 0), width=8, fill=(245, 245, 245))

    boxes = detect_panels(image)
    assert len(boxes) >= 1
    for box in boxes:
        assert box.right > box.left
        assert box.bottom > box.top
