from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.pipeline.export import export_project
from src.ui.state import get_project, persist_project
from src.utils.config import load_settings


def render() -> None:
    st.subheader("輸出影片")
    st.caption("輸出 9:16 Shorts 或 16:9 YouTube：MP4 + 字幕 + 下一集推薦片尾。")

    project = get_project()
    if not project or not project.panels:
        st.warning("請先完成前面步驟。")
        return

    settings = load_settings()
    aspect = st.radio(
        "輸出比例",
        options=["shorts", "youtube"],
        format_func=lambda x: "9:16 Shorts (1080×1920)" if x == "shorts" else "16:9 YouTube (1920×1080)",
        index=0 if project.aspect_ratio != "youtube" else 1,
        horizontal=True,
    )

    project.next_episode_title = st.text_input(
        "片尾標題",
        value=project.next_episode_title or settings["export"]["next_episode_title"],
    )
    project.next_episode_subtitle = st.text_input(
        "片尾副標",
        value=project.next_episode_subtitle or settings["export"]["next_episode_subtitle"],
    )

    if st.button("開始匯出", type="primary"):
        with st.spinner("渲染影格並呼叫 FFmpeg 匯出中…"):
            try:
                outputs = export_project(project, aspect_ratio=aspect)
                project.output_paths = outputs
                persist_project(project)
                st.success("匯出完成")
            except Exception as exc:
                st.error(str(exc))
                return
        st.rerun()

    outputs = project.output_paths or {}
    if not outputs:
        st.info("尚未匯出。請確認本機已安裝 ffmpeg。")
        return

    mp4 = outputs.get("mp4")
    srt = outputs.get("srt")
    end_card = outputs.get("end_card")

    if mp4 and Path(mp4).exists():
        st.video(mp4)
        st.download_button("下載 MP4", Path(mp4).read_bytes(), file_name=Path(mp4).name, mime="video/mp4")
    if srt and Path(srt).exists():
        st.download_button("下載 SRT 字幕", Path(srt).read_bytes(), file_name=Path(srt).name, mime="text/plain")
    if end_card and Path(end_card).exists():
        st.image(end_card, caption="下一集推薦片尾", width=360)
        st.download_button(
            "下載推薦片尾圖",
            Path(end_card).read_bytes(),
            file_name=Path(end_card).name,
            mime="image/png",
        )
