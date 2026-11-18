from src.pipeline.export import seconds_to_srt_ts, write_srt
from src.pipeline.motion import ken_burns_frame, resolve_canvas
from PIL import Image


def test_seconds_to_srt_ts():
    assert seconds_to_srt_ts(0) == "00:00:00,000"
    assert seconds_to_srt_ts(3661.5) == "01:01:01,500"


def test_write_srt(tmp_path):
    timeline = [
        {
            "kind": "panel",
            "speaker": "主角",
            "text": "嗨",
            "start": 0.0,
            "end": 2.0,
        },
        {
            "kind": "end_card",
            "speaker": "",
            "text": "下一集推薦 — 繼續觀看",
            "start": 2.0,
            "end": 5.0,
        },
    ]
    path = tmp_path / "out.srt"
    write_srt(timeline, path)
    content = path.read_text(encoding="utf-8")
    assert "主角: 嗨" in content
    assert "下一集推薦" in content


def test_ken_burns_frame_size():
    img = Image.new("RGB", (400, 300), (30, 30, 30))
    frame = ken_burns_frame(img, 108, 192, 0.5, "zoom_in")
    assert frame.size == (108, 192)


def test_resolve_canvas():
    w, h = resolve_canvas("shorts")
    assert w == 1080 and h == 1920
    w, h = resolve_canvas("youtube")
    assert w == 1920 and h == 1080
