# AI Motion Comic Studio

把漫畫頁面做成動態漫畫短影音的六步工作室：上傳 → AI 分鏡 → 台詞 OCR → 角色配音 → 運鏡字幕 → 輸出 Shorts / YouTube。

## 製作流程

1. **上傳漫畫圖片** — JPG / PNG  
2. **AI 分鏡切割** — 自動拆格 + 人工微調  
3. **台詞與劇本** — OCR + 人工校正  
4. **AI 角色配音** — edge-tts 語音（音效欄位預留）  
5. **動態漫畫** — Ken Burns 運鏡 + 字幕時間軸  
6. **輸出** — 9:16 Shorts / 16:9 YouTube（MP4 + SRT + 下一集推薦片尾）

## 環境需求

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/)（需可在終端機執行 `ffmpeg` / `ffprobe`）

## 安裝與啟動（Windows PowerShell）

```powershell
cd ai-motion-comic-studio
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

若 PowerShell 無法啟用虛擬環境：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 專案結構

```
app.py                 # Streamlit 六步 wizard
config/settings.yaml   # 解析度、音色、片尾文案
src/models/            # 專案 / 分鏡資料模型
src/pipeline/          # 上傳、分鏡、OCR、TTS、運鏡、匯出
src/ui/                # 各步驟介面
assets/projects/       # 執行時產生的專案檔（已 gitignore）
tests/                 # 單元測試
```

## 測試

```powershell
python -m pytest -q
```

## 版權提醒

請使用原創、已授權或公有領域的圖文影音素材。勿上傳未授權的商業漫畫或模仿受保護聲線。
