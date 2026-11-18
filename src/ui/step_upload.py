from __future__ import annotations

import streamlit as st

from src.pipeline.upload import create_project_from_upload, load_page_image
from src.ui.state import get_project, list_saved_projects, persist_project, reload_project


def render() -> None:
    st.subheader("上傳漫畫圖片")
    st.caption("支援 JPG / PNG。請只上傳你擁有權利或已授權使用的作品。")

    saved = list_saved_projects()
    if saved:
        options = {f"{title} ({pid})": pid for pid, title in saved}
        choice = st.selectbox("或載入既有專案", ["（新建）"] + list(options.keys()))
        if choice != "（新建）" and st.button("載入專案"):
            reload_project(options[choice])
            st.success(f"已載入專案 {options[choice]}")
            st.rerun()

    title = st.text_input("專案名稱", value=(get_project().title if get_project() else "我的動態漫畫"))
    uploaded = st.file_uploader("上傳漫畫頁面", type=["png", "jpg", "jpeg"], key="page_uploader")

    if uploaded is not None and st.button("建立 / 更新專案", type="primary"):
        project = create_project_from_upload(uploaded.name, uploaded.getvalue(), title=title)
        persist_project(project)
        st.success(f"專案已建立：{project.id}")
        st.rerun()

    project = get_project()
    if project and project.page_image_path:
        image = load_page_image(project)
        st.image(image, caption=f"{project.title}（{image.width} × {image.height}）", use_container_width=True)
        if st.button("前往分鏡切割 →"):
            st.session_state.step = 1
            st.rerun()
    else:
        st.info("請先上傳一張漫畫頁面以開始流程。")
