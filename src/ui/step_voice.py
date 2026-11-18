from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.pipeline.ocr import update_dialogue
from src.pipeline.tts import generate_panel_audio, generate_project_audio
from src.ui.state import get_project, persist_project
from src.utils.config import load_settings


def render() -> None:
    st.subheader("AI 角色配音")
    st.caption("使用 edge-tts 產生語音；音效欄位先記錄需求，後續可接素材庫。")

    project = get_project()
    if not project or not project.panels:
        st.warning("請先完成台詞步驟。")
        return

    settings = load_settings()
    voices = settings["tts"]["voices"]
    voice_labels = {v["id"]: v["label"] for v in voices}
    voice_ids = list(voice_labels.keys())

    c1, c2 = st.columns(2)
    if c1.button("為全部台詞產生配音", type="primary"):
        with st.spinner("TTS 產生中…"):
            project = generate_project_audio(project, force=True)
            persist_project(project)
        st.success("全部配音完成")
        st.rerun()
    if c2.button("只補產生缺少的配音"):
        with st.spinner("TTS 產生中…"):
            project = generate_project_audio(project, force=False)
            persist_project(project)
        st.success("缺少的配音已補齊")
        st.rerun()

    for panel in project.panels:
        dialogue = panel.dialogue
        with st.expander(f"{panel.id} — {dialogue.speaker if dialogue else ''}", expanded=True):
            cols = st.columns([1, 2])
            if panel.image_path:
                cols[0].image(panel.image_path, use_container_width=True)
            with cols[1]:
                st.write(dialogue.text if dialogue and dialogue.text else "（尚無台詞）")
                current_voice = dialogue.voice_id if dialogue and dialogue.voice_id in voice_ids else voice_ids[0]
                voice = st.selectbox(
                    "音色",
                    voice_ids,
                    index=voice_ids.index(current_voice),
                    format_func=lambda vid: voice_labels.get(vid, vid),
                    key=f"tts_voice_{panel.id}",
                )
                sfx = st.text_input(
                    "音效備註（預留）",
                    value=dialogue.sfx_note if dialogue else "",
                    key=f"sfx_{panel.id}",
                )
                b1, b2 = st.columns(2)
                if b1.button("儲存設定", key=f"voice_save_{panel.id}"):
                    project = update_dialogue(project, panel.id, voice_id=voice, sfx_note=sfx)
                    persist_project(project)
                    st.success("已儲存")
                if b2.button("重新產生此格", key=f"voice_gen_{panel.id}"):
                    project = update_dialogue(project, panel.id, voice_id=voice, sfx_note=sfx)
                    with st.spinner("產生中…"):
                        project = generate_panel_audio(project, panel.id)
                        persist_project(project)
                    st.success("已產生")
                    st.rerun()

                audio_path = dialogue.audio_path if dialogue else None
                if audio_path and Path(audio_path).exists():
                    st.audio(audio_path)
                else:
                    st.caption("尚未產生音訊")

    if st.button("前往動態漫畫 →"):
        st.session_state.step = 4
        st.rerun()
