from __future__ import annotations

import streamlit as st

from src.pipeline.ocr import run_ocr_for_project, update_dialogue
from src.ui.state import get_project, persist_project
from src.utils.config import load_settings


def render() -> None:
    st.subheader("台詞與劇本")
    st.caption("OCR 自動辨識後可人工校正 speaker、台詞與時長。")

    project = get_project()
    if not project or not project.panels:
        st.warning("請先完成分鏡切割。")
        return

    settings = load_settings()
    voices = settings["tts"]["voices"]
    voice_labels = {v["id"]: v["label"] for v in voices}

    c1, c2 = st.columns(2)
    if c1.button("對所有空台詞執行 OCR", type="primary"):
        with st.spinner("OCR 辨識中（首次會下載模型，請稍候）…"):
            project = run_ocr_for_project(project, overwrite_empty_only=True)
            persist_project(project)
        st.success("OCR 完成")
        st.rerun()
    if c2.button("重新 OCR 覆蓋全部"):
        with st.spinner("OCR 辨識中…"):
            project = run_ocr_for_project(project, overwrite_empty_only=False)
            persist_project(project)
        st.success("已覆蓋全部台詞")
        st.rerun()

    for panel in project.panels:
        dialogue = panel.dialogue
        with st.expander(f"{panel.id}", expanded=True):
            cols = st.columns([1, 2])
            if panel.image_path:
                cols[0].image(panel.image_path, use_container_width=True)
            with cols[1]:
                speaker = st.text_input("角色 / 旁白", value=dialogue.speaker if dialogue else "旁白", key=f"sp_{panel.id}")
                text = st.text_area("台詞", value=dialogue.text if dialogue else "", height=120, key=f"tx_{panel.id}")
                duration = st.number_input(
                    "時長提示（秒）",
                    min_value=0.5,
                    max_value=30.0,
                    value=float(dialogue.duration_hint if dialogue else 3.0),
                    step=0.5,
                    key=f"du_{panel.id}",
                )
                voice_ids = list(voice_labels.keys())
                current_voice = dialogue.voice_id if dialogue and dialogue.voice_id in voice_ids else voice_ids[0]
                voice = st.selectbox(
                    "預設音色",
                    voice_ids,
                    index=voice_ids.index(current_voice),
                    format_func=lambda vid: voice_labels.get(vid, vid),
                    key=f"vo_{panel.id}",
                )
                if st.button("儲存此格", key=f"save_{panel.id}"):
                    project = update_dialogue(
                        project,
                        panel.id,
                        speaker=speaker,
                        text=text,
                        voice_id=voice,
                        duration_hint=float(duration),
                    )
                    persist_project(project)
                    st.success("已儲存")

    if st.button("前往配音 →"):
        st.session_state.step = 3
        st.rerun()
