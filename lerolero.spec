# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ['pynput.keyboard._win32', 'pynput.mouse._win32']

# Only bundle the lightweight app code + customtkinter UI
for pkg in ('lerolero', 'customtkinter'):
    try:
        tmp = collect_all(pkg)
        datas += tmp[0]; binaries += tmp[1]; hiddenimports += tmp[2]
    except Exception:
        pass

# Exclude ALL heavy ML deps — they're installed at runtime via runtime_setup.py
EXCLUDE_HEAVY = [
    'torch', 'torchvision', 'torchaudio', 'torch._C', 'torch.cuda',
    'caffe2', 'functorch',
    'openvino', 'optimum', 'optimum_intel',
    'transformers', 'tokenizers', 'safetensors',
    'huggingface_hub', 'accelerate',
    'onnxruntime', 'onnx',
    'scipy', 'scipy.special',
    'tqdm',
]

a = Analysis(
    ['src\\lerolero\\__main__.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDE_HEAVY,
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
