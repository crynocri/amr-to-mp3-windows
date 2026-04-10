# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH).resolve().parents[1]
entry_file = project_root / "amr_to_mp3" / "__main__.py"

binaries = []
for candidate in (
    project_root / "vendor" / "ffmpeg" / "ffmpeg.exe",
    project_root / "vendor" / "ffmpeg.exe",
):
    if candidate.exists():
        binaries.append((str(candidate), "."))
        break


a = Analysis(
    [str(entry_file)],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name="AMRToMP3",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
