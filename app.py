import hashlib
import io
import zipfile

import streamlit as st
from PIL import Image, ImageDraw
from streamlit_cropper import st_cropper

st.set_page_config(page_title="AI Motion Comic Studio", layout="wide")
st.title("🎬 AI Motion Comic Studio")
st.caption("Mouse-driven panel cropping · Use only artwork you have rights to use.")

uploaded = st.file_uploader("Upload a comic page (PNG/JPG)", type=["png", "jpg", "jpeg"])
if uploaded is None:
    st.info("Upload a comic page to begin.")
    st.stop()

raw = uploaded.getvalue()
image_id = hashlib.sha256(raw).hexdigest()
image = Image.open(io.BytesIO(raw)).convert("RGB")
if st.session_state.get("image_id") != image_id:
    st.session_state.image_id = image_id
    st.session_state.panels = []

left, right = st.columns([3, 2])
with left:
    st.subheader("1. Drag the crop handles")
    st.write("Move and resize the rectangle, then click **Add panel**. Repeat for each frame.")
    crop = st_cropper(
        image,
        realtime_update=True,
        box_color="#00D4FF",
        aspect_ratio=None,
        return_type="box",
        key=f"crop_{image_id}",
    )
    x = max(0, int(crop["left"]))
    y = max(0, int(crop["top"]))
    w = max(0, int(crop["width"]))
    h = max(0, int(crop["height"]))
    x2 = min(image.width, x + w)
    y2 = min(image.height, y + h)
    st.caption(f"Selected: ({x}, {y}) → ({x2}, {y2}) · Image: {image.width}×{image.height}")
    if st.button("➕ Add panel", type="primary"):
        if x2 <= x or y2 <= y:
            st.error("Select a non-empty rectangle first.")
        else:
            st.session_state.panels.append((x, y, x2, y2))
            st.success(f"Panel {len(st.session_state.panels)} added.")
    if st.button("↩️ Undo last panel", disabled=not st.session_state.panels):
        st.session_state.panels.pop()
        st.rerun()
    if st.button("🗑️ Clear all", disabled=not st.session_state.panels):
        st.session_state.panels = []
        st.rerun()

with right:
    st.subheader(f"2. Preview panels ({len(st.session_state.panels)})")
    if not st.session_state.panels:
        st.info("No panels yet. Select a region and click Add panel.")
    for i, box in enumerate(st.session_state.panels, 1):
        st.image(image.crop(box), caption=f"Panel {i}: {box}", use_container_width=True)

if st.session_state.panels:
    st.subheader("3. Export")
    preview = image.copy()
    draw = ImageDraw.Draw(preview)
    for i, box in enumerate(st.session_state.panels, 1):
        draw.rectangle(box, outline="#00D4FF", width=4)
        draw.text((box[0] + 5, box[1] + 5), str(i), fill="#FF0000")
    st.image(preview, caption="Panel positions", use_container_width=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for i, box in enumerate(st.session_state.panels, 1):
            panel_bytes = io.BytesIO()
            image.crop(box).save(panel_bytes, format="PNG")
            archive.writestr(f"panel_{i:02d}.png", panel_bytes.getvalue())
    st.download_button(
        "⬇️ Download all panels (ZIP)",
        data=buffer.getvalue(),
        file_name="comic_panels.zip",
        mime="application/zip",
    )
