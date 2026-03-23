# LeroLero — Project Context for Claude Code

## What is this?
LeroLero is a 100% offline speech-to-text desktop app for Windows. The user speaks, it transcribes via Whisper (OpenVINO/CUDA/DirectML), and pastes into the active window. No data ever leaves the machine.

## Architecture
- **Backend:** Python (unchanged core)
  - `src/lerolero/app_controller.py` — main controller, hotkeys, recording flow, tray
  - `src/lerolero/transcriber.py` — Whisper via OpenVINO (Intel), CUDA (NVIDIA), DirectML (AMD), or CPU
  - `src/lerolero/overlay_container.py` — floating overlay (tkinter, runs in own thread)
  - `src/lerolero/metrics.py` — session metrics, JSONL storage
  - `src/lerolero/paths.py` — AppData paths (%APPDATA%/LeroLero)
  - `src/lerolero/text_cleaner.py` — removes stutters/fillers post-transcription
  - `src/lerolero/context_prompts.py` — vocabulary hints based on active app (VS Code, Chrome, etc.)
  - `src/lerolero/webview_bridge.py` — pywebview bridge (Python↔React)
- **Frontend:** React + TypeScript + Tailwind CSS + Framer Motion (in `web/`)
  - Rendered via pywebview (WebView2 on Windows, no network)
  - `web/src/App.tsx` — main layout with sidebar + tabs
  - `web/src/views/` — GeneralView (chat+history), MetricsView, SettingsView, AboutView
  - `web/src/components/` — ChatBubble, Sidebar, StatusPill, VoiceOrb, Preloader
  - `web/src/lib/api.ts` — bridge to Python via window.pywebview.api

## Key Design Decisions
- **Offline first:** Zero network calls after initial model download. No cloud APIs.
- **Multi-GPU:** Auto-detects Intel (OpenVINO), NVIDIA (CUDA), AMD (DirectML), falls back to CPU.
- **pywebview over Electron:** Lighter, uses system WebView2, no Chromium bundle.
- **CustomTkinter kept as fallback:** `gui/` folder still exists for systems without pywebview.
- **Data in AppData:** config.json, history/, metrics all in %APPDATA%/LeroLero, not cwd.
- **Window title tracking:** Each transcription records which app was active for filtering.
- **Audio saving:** Optional .wav recording toggle in settings.
- **Translate hotkey:** Separate hotkey for record+translate-to-English.
- **Tray menu in Portuguese:** "Abrir LeroLero", "Pausar / Retomar", "Sair".

## How to Run
```bash
# Development
cd web && npm run build   # build React frontend
uv run lerolero           # launch app

# Or just
./run.bat                 # Windows double-click
```

## How to Build .exe
```powershell
./build_dist.ps1
# Output: dist/LeroLero/LeroLero.exe (~76MB, downloads ML deps on first run)
```

## Brand
- Name: **LeroLero** (always together, both L's capitalized)
- Font: Modak (for branding text)
- Icon: Custom bubble pattern icon (assets/icon.ico, icon.png)
- Colors: Dark theme default, purple accent (#b4a0ff dark / #4c2fbd light)

## User Preferences
- Language: Portuguese (BR) for UI, but code/comments in English
- The user values: minimalism, performance, privacy, working features over half-baked animations
- Remove features that don't work well rather than shipping broken ones
- Settings should always be inline (not modal windows)
- The user has an Intel Arc B580 GPU — OpenVINO is the primary backend

## Git
- Remote `lerolero` → https://github.com/nicolasf9/lerolero.git
- Branch: `main-lerolero` pushes to `lerolero/main`
- Remote `origin` → https://github.com/rpfilomeno/whisper-typing.git (upstream fork)
