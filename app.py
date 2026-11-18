from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui import step_export, step_motion, step_panels, step_script, step_upload, step_voice
from src.ui.state import STEPS, get_project, init_session

st.set_page_config(page_title="AI Motion Comic Studio", layout="wide", page_icon="🎬")
init_session()

st.title("AI Motion Comic Studio")
st.caption("自動化製作流程：上傳 → 分鏡 → 台詞 → 配音 → 動態 → 輸出 Shorts / YouTube")

# Pipeline overview
with st.container():
    overview = st.columns(6)
    labels = [
        ("上傳漫畫圖片", "JPG / PNG"),
        ("AI 分鏡切割", "拆解每格畫面"),
        ("台詞與劇本", "OCR + 人工校正"),
        ("AI 角色配音", "語音與音效"),
        ("動態漫畫", "運鏡、字幕、特效"),
        ("輸出影片", "9:16 / 16:9 MP4"),
    ]
    for col, (title, subtitle) in zip(overview, labels):
        col.markdown(f"**{title}**")
        col.caption(subtitle)

st.divider()

step_labels = [label for _, label in STEPS]
st.radio(
    "製作步驟",
    options=list(range(len(STEPS))),
    format_func=lambda i: step_labels[i],
    horizontal=True,
    key="step",
)

project = get_project()
if project:
    st.sidebar.success(f"專案：{project.title}")
    st.sidebar.caption(f"ID：{project.id}")
    st.sidebar.caption(f"分鏡數：{len(project.panels)}")
else:
    st.sidebar.info("尚未建立專案")

st.sidebar.markdown("### 流程")
for i, (_, label) in enumerate(STEPS):
    mark = "→" if i == st.session_state.step else "•"
    st.sidebar.write(f"{mark} {label}")

renderers = [
    step_upload.render,
    step_panels.render,
    step_script.render,
    step_voice.render,
    step_motion.render,
    step_export.render,
]
renderers[st.session_state.step]()
