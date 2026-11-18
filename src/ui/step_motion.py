from __future__ import annotations

import streamlit as st

from src.pipeline.motion import build_timeline, update_motion_styles
from src.ui.state import get_project, persist_project
from src.utils.config import load_settings


STYLE_LABELS = {
    "zoom_in": "推近 Zoom In",
    "zoom_out": "拉遠 Zoom Out",
    "pan_left": "左移 Pan Left",
    "pan_right": "右移 Pan Right",
}


def render() -> None:
    st.subheader("動態漫畫")
    st.caption("為每格選擇運鏡，並預覽字幕時間軸。")

    project = get_project()
    if not project or not project.panels:
        st.warning("請先完成前面步驟。")
        return

    settings = load_settings()
    styles = settings["motion"]["styles"]

    st.markdown("#### 運鏡設定")
    new_styles: dict[str, str] = {}
    for panel in project.panels:
        current = panel.motion_style if panel.motion_style in styles else styles[0]
        choice = st.selectbox(
            f"{panel.id} 運鏡",
            styles,
            index=styles.index(current),
            format_func=lambda s: STYLE_LABELS.get(s, s),
            key=f"motion_{panel.id}",
        )
        new_styles[panel.id] = choice
        if panel.image_path:
            st.image(panel.image_path, width=220)

    if st.button("儲存運鏡", type="primary"):
        project = update_motion_styles(project, new_styles)
        persist_project(project)
        st.success("運鏡已儲存")

    st.markdown("#### 字幕時間軸預覽")
    timeline = build_timeline(project)
    rows = []
    for entry in timeline:
        rows.append(
            {
                "類型": "片尾推薦" if entry["kind"] == "end_card" else "分鏡",
                "ID": entry["panel_id"],
                "開始(s)": round(entry["start"], 2),
                "結束(s)": round(entry["end"], 2),
                "時長(s)": round(entry["duration"], 2),
                "運鏡": entry.get("motion_style", ""),
                "角色": entry.get("speaker", ""),
                "字幕": (entry.get("text") or "")[:80],
            }
        )
    st.dataframe(rows, use_container_width=True)

    total = timeline[-1]["end"] if timeline else 0
    st.info(f"預估總時長約 {total:.1f} 秒（含推薦片尾）")

    if st.button("前往輸出 →"):
        st.session_state.step = 5
        st.rerun()
