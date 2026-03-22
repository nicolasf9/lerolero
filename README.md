# LeroLero

**Speak and it types.** 100% offline speech-to-text for Windows.

LeroLero runs entirely on your machine -- your voice never leaves your computer. It uses OpenAI's Whisper model locally via your GPU (Intel, NVIDIA, or AMD) or CPU.

## Features

- **100% Offline** -- no cloud, no API keys, no data leaves your PC
- **Multi-GPU** -- auto-detects Intel Arc (OpenVINO), NVIDIA (CUDA), AMD (DirectML), or CPU
- **Multilingual** -- supports Portuguese, English, and 90+ languages simultaneously
- **Live Typing** -- types in real-time as you speak, or pastes when done
- **Chat-Style UI** -- fullscreen dark/light interface showing your transcriptions like a chat
- **Metrics Dashboard** -- tracks words spoken, time saved, daily streaks
- **Audio Waveform Overlay** -- floating indicator with real-time audio visualization
- **System Tray** -- runs in background, activated by global hotkey
- **Windows Startup** -- can auto-start with Windows

## Quick Start

### Prerequisites

- **Python 3.13.7+** (via [uv](https://docs.astral.sh/uv/))
- **Windows 10/11**

### Install

```bash
# Install uv if you don't have it
pip install uv

# Clone
git clone https://github.com/nicolasf9/lerolero.git
cd lerolero
```

### Choose your GPU

```bash
# Intel Arc / Intel iGPU
uv pip install -e ".[intel]"

# NVIDIA (CUDA)
uv pip install -e ".[nvidia]"

# AMD (DirectML)
uv pip install -e ".[amd]"

# CPU only (no GPU acceleration)
uv pip install -e .
```

### Run

```bash
uv run lerolero
```

## Usage

1. Press **F9** (default hotkey) to start recording
2. Speak in any language
3. Release to stop (hold mode) or press F9 again (toggle mode)
4. Text appears in the chat and is typed/pasted into the active window

### Settings

Click the gear icon to configure: Whisper model, language, device, recording mode, hotkey, theme (dark/light), auto-start with Windows.

## GPU Support

| GPU | Backend | Install extra |
|-----|---------|---------------|
| Intel Arc B580, A770, etc. | OpenVINO | `.[intel]` |
| NVIDIA RTX/GTX | CUDA | `.[nvidia]` |
| AMD RX 7000/6000 | DirectML | `.[amd]` |
| CPU only | PyTorch | base install |

The app auto-detects your GPU and selects the best backend.

## Privacy

Zero network calls after initial model download. All transcription runs locally. No telemetry, no analytics, no tracking.

## Build Executable

```powershell
.\build_dist.ps1
```

Creates `dist/lerolero/lerolero.exe` -- standalone, no Python needed.

## Credits

Based on [whisper-typing](https://github.com/rpfilomeno/whisper-typing) by Roger Filomeno (MIT License).

## License

MIT -- see [LICENSE](LICENSE)
