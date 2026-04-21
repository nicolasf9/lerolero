# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

datas = []
binaries = []
hiddenimports = [
    'pynput.keyboard._win32', 'pynput.mouse._win32',
    'webview',
    'clr_loader', 'pythonnet',
    'onnx_asr',
    'onnxruntime',
    'onnxruntime.capi.onnxruntime_providers_openvino',
]

# Bundle everything needed — onnxruntime-openvino and onnx-asr are NOT excluded.
# The user gets a complete, offline-ready app on first install.
for pkg in ('lerolero', 'webview', 'clr_loader', 'pythonnet',
            'onnxruntime', 'onnx_asr', 'huggingface_hub'):
    try:
        tmp = collect_all(pkg)
        datas += tmp[0]; binaries += tmp[1]; hiddenimports += tmp[2]
    except Exception:
        pass

# Include the React web/dist build
web_dist = os.path.join('web', 'dist')
if os.path.exists(web_dist):
    datas += [(web_dist, os.path.join('lerolero', 'web_dist'))]

# Include assets
datas += [('src/lerolero/assets/icon.ico', 'lerolero/assets')]
datas += [('src/lerolero/assets/icon.png', 'lerolero/assets')]

a = Analysis(
    ['src\\lerolero\\__main__.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_pythonnet.py'],
    excludes=[
        # Explicitly exclude heavy packages we no longer use
        'torch', 'torchvision', 'torchaudio',
        'transformers', 'tokenizers', 'safetensors',
        'optimum', 'optimum_intel', 'optimum.onnxruntime',
        'accelerate', 'scipy',
        'customtkinter',  # CTk fallback removed
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LeroLero',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/lerolero/assets/icon.ico',
    uac_admin=False,
    version='version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LeroLero',
)
