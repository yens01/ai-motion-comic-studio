# AI Motion Comic Studio

An incremental, rights-aware pipeline for turning original comic panels into motion-comic videos.

## Current MVP
- Upload JPG/PNG comic page
- Manually enter panel crop rectangles and preview results
- Download all cropped panels as a ZIP

OCR, voice, video rendering and recommendations are **planned**, not yet implemented.

## Run (Windows PowerShell)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
If PowerShell blocks activation, run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe -m streamlit run app.py` instead.

## Roadmap
1. Automated frame segmentation with manual override
2. OCR + editable dialogue / subtitle timeline
3. TTS voice and licensed sound effects
4. FFmpeg pan/zoom, transitions, subtitles and MP4 output
5. End-screen recommendation cards / playlist metadata

## Copyright
Use original, licensed or public-domain artwork, music and voices. Do not upload copyrighted franchise pages or imitate performers' voices without appropriate permissions.
