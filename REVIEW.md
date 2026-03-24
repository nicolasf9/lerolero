# LeroLero — Code Review (2026-03-24)

## Critical Bugs

| # | File | Issue |
|---|------|-------|
| 1 | `tests/test_*.py` | All tests import `whisper_typing` instead of `lerolero` — no test runs |
| 2 | `web/src/components/ChatBubble.tsx:23` | RegExp with `g` flag + `.test()` after `.split()` — search highlighting breaks intermittently |
| 3 | `.github/workflows/build.yaml` | Tests commented out in CI — zero regression protection |
| 4 | `web/tsconfig.json` | References `tsconfig.app.json` and `tsconfig.node.json` that don't exist in repo |

## Security

| # | File | Issue |
|---|------|-------|
| 5 | `webview_bridge.py:204` | `get_audio_base64(filename)` has no path traversal validation — could read arbitrary files via `../../../` |
| 6 | `app_controller.py:213` | Inline `pip install` without version pinning |

## Concurrency / Stability

| # | File | Issue |
|---|------|-------|
| 7 | `app_controller.py:516-546` | Race condition in `_live_transcription_loop` — accesses `self.recorder` without lock |
| 8 | `app_controller.py:405` | Daemon thread with no exception handling — fails silently |
| 9 | `ChatBubble.tsx:47-70` | Audio player has no guard against rapid double-click |

## Code Quality

| # | Area | Issue |
|---|------|-------|
| 10 | Backend | Bare `except Exception: pass` in ~6 locations — hinders debugging |
| 11 | Backend | Magic numbers scattered (0.005s, 0.7s, 0.8s) — should be named constants |
| 12 | Backend | `_has_speech` accessed as private attribute (`noqa: SLF001`) |
| 13 | Frontend | `as any` in api.ts, App.tsx — defeats TypeScript safety |
| 14 | Frontend | `Record<string, any>` for config — no typed interface |
| 15 | Frontend | No Error Boundaries — any error = white screen |
| 16 | Frontend | History list not virtualized — may lag with 1000+ items |

## Accessibility

- Selects missing associated `<label>` (GeneralView, SettingsView)
- Sidebar has no keyboard navigation (tab+enter)
- `<img alt="">` on logo — should be `alt="LeroLero logo"`

## Dead Code / Legacy

- `gui/` folder (CustomTkinter) — fallback that likely no longer works
- Explicit removal of `gemini_api_key` in config — cleanup of removed feature
- `os._exit(0)` in tray — should be `sys.exit(0)`

## What's Done Well

- Clean backend/frontend separation (pywebview bridge)
- Elegant multi-GPU auto-detection (OpenVINO > CUDA > DirectML > CPU)
- Well-documented regex in `text_cleaner.py`
- Clean JSONL storage in `metrics.py`
- Proper useEffect cleanup and dependency arrays in React
- Performant Framer Motion animations
- Dark mode with CSS variables
- 100% offline, privacy-first design

## Suggested Priorities

1. **Fix test imports** (`whisper_typing` → `lerolero`) and re-enable CI
2. **Validate path traversal** in `get_audio_base64`
3. **Add thread locks** for shared state between threads
4. **Fix RegExp bug** in ChatBubble search highlighting
5. **Type config** in frontend (interface instead of `Record<string, any>`)
6. **Remove `gui/` folder** if pywebview is the definitive default
