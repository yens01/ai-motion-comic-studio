from src.models.project import Panel, PanelBox, Project


def test_panel_box_clamp():
    box = PanelBox(-10, -5, 500, 400).clamp(200, 100)
    assert box.left == 0
    assert box.top == 0
    assert box.right == 200
    assert box.bottom == 100


def test_project_roundtrip(tmp_path):
    project = Project.create("測試專案")
    project.page_width = 100
    project.page_height = 200
    project.panels = [Panel.create(0, PanelBox(0, 0, 50, 80))]
    project.panels[0].dialogue.text = "你好"
    project.save(tmp_path)

    loaded = Project.load(tmp_path)
    assert loaded.title == "測試專案"
    assert loaded.page_width == 100
    assert len(loaded.panels) == 1
    assert loaded.panels[0].dialogue.text == "你好"
    assert loaded.panels[0].box.as_tuple() == (0, 0, 50, 80)
