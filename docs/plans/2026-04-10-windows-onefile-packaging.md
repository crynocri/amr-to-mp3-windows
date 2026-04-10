# Windows Onefile Packaging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Switch the Windows release from PyInstaller one-folder packaging to a single `AMRToMP3.exe` while preserving bundled ffmpeg support and CI smoke coverage.

**Architecture:** Keep the current conversion flow based on invoking `ffmpeg`, but change the PyInstaller spec to onefile mode so bundled binaries are extracted into the PyInstaller temp directory at runtime. Add a small hidden CLI probe so CI can verify the bundled ffmpeg from the final single executable without launching the GUI.

**Tech Stack:** Python 3.12, unittest, PyInstaller, GitHub Actions, PowerShell

### Task 1: Add entrypoint probe behavior

**Files:**
- Modify: `amr_to_mp3/__main__.py`
- Test: `tests/test_entrypoint.py`

**Step 1: Write the failing test**

`tests/test_entrypoint.py` already contains `test_main_probe_ffmpeg_exits_without_launching_gui`.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_entrypoint.EntryPointTests.test_main_probe_ffmpeg_exits_without_launching_gui -v`
Expected: FAIL because `--probe-ffmpeg` is not recognized yet.

**Step 3: Write minimal implementation**

Add a hidden `--probe-ffmpeg` flag in `amr_to_mp3/__main__.py`. When present, resolve the bundled ffmpeg path, run `ffmpeg -version`, print a short success line, and return without loading the GUI.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_entrypoint.EntryPointTests.test_main_probe_ffmpeg_exits_without_launching_gui -v`
Expected: PASS

### Task 2: Switch PyInstaller spec to onefile

**Files:**
- Modify: `build/windows/amr_to_mp3.spec`
- Test: `tests/test_windows_packaging.py`

**Step 1: Write the failing test**

`tests/test_windows_packaging.py` already contains `test_spec_uses_pyinstaller_onefile_mode`.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_windows_packaging.WindowsPackagingConfigTests.test_spec_uses_pyinstaller_onefile_mode -v`
Expected: FAIL because the spec still uses `exclude_binaries=True` and `COLLECT(...)`.

**Step 3: Write minimal implementation**

Update the spec so `EXE(...)` includes `a.binaries` and `a.datas`, sets `exclude_binaries=False`, and removes the `COLLECT(...)` block.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_windows_packaging.WindowsPackagingConfigTests.test_spec_uses_pyinstaller_onefile_mode -v`
Expected: PASS

### Task 3: Update CI smoke verification for the onefile artifact

**Files:**
- Modify: `.github/workflows/windows-package.yml`
- Test: `tests/test_windows_packaging.py`

**Step 1: Write the failing test**

`tests/test_windows_packaging.py` already contains `test_workflow_smoke_tests_bundled_ffmpeg_after_packaging`.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_windows_packaging.WindowsPackagingConfigTests.test_workflow_smoke_tests_bundled_ffmpeg_after_packaging -v`
Expected: FAIL because the workflow still probes `dist\\AMRToMP3\\_internal\\ffmpeg.exe`.

**Step 3: Write minimal implementation**

Update the workflow to smoke test the final single executable with `.\dist\AMRToMP3.exe --probe-ffmpeg` and upload the single exe as the artifact.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_windows_packaging.WindowsPackagingConfigTests.test_workflow_smoke_tests_bundled_ffmpeg_after_packaging -v`
Expected: PASS

### Task 4: Run focused regression checks

**Files:**
- Verify: `tests/test_entrypoint.py`
- Verify: `tests/test_windows_packaging.py`

**Step 1: Run focused suite**

Run: `python3 -m unittest tests.test_entrypoint tests.test_windows_packaging -v`
Expected: all tests PASS.

**Step 2: Sanity-check build script assumptions**

Run: `python3 -m unittest tests.test_windows_packaging.WindowsPackagingConfigTests.test_build_script_validates_bundled_ffmpeg_before_packaging -v`
Expected: PASS

### Task 5: Update packaging docs if needed

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`

**Step 1: Confirm whether docs still describe one-folder output**

Run: `rg -n "dist/AMRToMP3|_internal|one-folder|解压" AGENTS.md README.md`
Expected: any outdated one-folder references are identified.

**Step 2: Write minimal doc updates**

Adjust artifact layout and smoke-test instructions only where needed so docs match the onefile build.

**Step 3: Verify docs**

Run: `rg -n "AMRToMP3.exe|onefile|_internal" AGENTS.md README.md`
Expected: docs reflect the chosen packaging mode accurately.
