from __future__ import annotations

import streamlit as st

from src.models.project import PanelBox
from src.pipeline.panels import (
    add_panel,
    apply_boxes_to_project,
    detect_panels,
    remove_panel,
    update_panel_box,
)
from src.pipeline.upload import load_page_image
from src.ui.state import get_project, persist_project
from src.utils.images import draw_boxes


def render() -> None:
    st.subheader("AI 分鏡切割")
    st.caption("自動拆解每格畫面，並可人工微調座標。")

    project = get_project()
    if not project or not project.page_image_path:
        st.warning("請先完成上傳步驟。")
        return

    image = load_page_image(project)

    cols = st.columns([1, 1, 1, 1])
    if cols[0].button("自動偵測分鏡", type="primary"):
        boxes = detect_panels(image)
        project = apply_boxes_to_project(project, image, boxes)
        persist_project(project)
        st.success(f"偵測到 {len(boxes)} 格")
        st.rerun()

    if cols[1].button("新增一格"):
        project = add_panel(project, image)
        persist_project(project)
        st.rerun()

    if cols[2].button("整頁單格"):
        project = apply_boxes_to_project(project, image, [PanelBox(0, 0, image.width, image.height)])
        persist_project(project)
        st.rerun()

    if not project.panels:
        st.info("尚未有分鏡，請先執行自動偵測或新增。")
        return

    boxes = [p.box.as_tuple() for p in project.panels]
    labels = [str(i + 1) for i in range(len(project.panels))]
    st.image(draw_boxes(image, boxes, labels), caption="分鏡預覽", use_container_width=True)

    for i, panel in enumerate(project.panels):
        with st.expander(f"分鏡 {i + 1} — {panel.id}", expanded=(i == 0)):
            a, b, c, d = st.columns(4)
            left = a.number_input("Left", 0, image.width - 1, panel.box.left, key=f"pl{i}")
            top = b.number_input("Top", 0, image.height - 1, panel.box.top, key=f"pt{i}")
            right = c.number_input("Right", 1, image.width, panel.box.right, key=f"pr{i}")
            bottom = d.number_input("Bottom", 1, image.height, panel.box.bottom, key=f"pb{i}")

            preview_cols = st.columns([2, 1])
            if panel.image_path:
                preview_cols[0].image(panel.image_path, width=280)
            if preview_cols[1].button("套用座標", key=f"apply{i}"):
                if right <= left or bottom <= top:
                    st.error("Right 須大於 Left，Bottom 須大於 Top")
                else:
                    project = update_panel_box(project, image, i, PanelBox(int(left), int(top), int(right), int(bottom)))
                    persist_project(project)
                    st.rerun()
            if preview_cols[1].button("刪除", key=f"del{i}"):
                project = remove_panel(project, image, i)
                persist_project(project)
                st.rerun()

    if st.button("前往台詞與劇本 →"):
        st.session_state.step = 2
        st.rerun()
