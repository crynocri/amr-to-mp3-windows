# AMR To MP3 GUI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a minimal Windows-friendly desktop app that converts `.amr` files to `.mp3` for single-file and batch workflows.

**Architecture:** Use a thin Tkinter GUI over a small conversion core. The core owns input validation, ffmpeg discovery, task planning, subprocess execution, and result reporting. The GUI owns file selection, output directory selection, background execution, and user-facing logs.

**Tech Stack:** Python 3.11+, Tkinter, stdlib `unittest`, ffmpeg, PyInstaller for Windows packaging.

### Task 1: Create the failing tests for conversion planning

**Files:**
- Create: `tests/test_converter.py`
- Create: `tests/test_helpers.py`
- Create: `amr_to_mp3/__init__.py`
- Test: `tests/test_converter.py`

**Step 1: Write the failing tests**

```python
def test_plan_single_file_defaults_to_source_directory(self):
    request = plan_conversion(Path("voice.amr"), None)
    self.assertEqual(request.output_path.name, "voice.mp3")

def test_plan_batch_skips_non_amr_files(self):
    plan = plan_batch([Path("a.amr"), Path("b.txt")], Path("out"))
    self.assertEqual([item.input_path.name for item in plan], ["a.amr"])
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_converter -v`
Expected: FAIL because the `amr_to_mp3.converter` module does not exist yet.

**Step 3: Write minimal implementation**

```python
@dataclass
class ConversionTask:
    input_path: Path
    output_path: Path
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_converter -v`
Expected: PASS for the initial planning cases.

### Task 2: Add failing tests for ffmpeg execution and errors

**Files:**
- Modify: `tests/test_converter.py`
- Modify: `tests/test_helpers.py`
- Create: `amr_to_mp3/converter.py`
- Test: `tests/test_converter.py`

**Step 1: Write the failing tests**

```python
def test_convert_file_runs_ffmpeg_and_creates_output(self):
    result = convert_file(task, ffmpeg_path=fake_ffmpeg)
    self.assertTrue(result.succeeded)

def test_convert_batch_collects_failures(self):
    summary = convert_batch(tasks, ffmpeg_path=fake_ffmpeg)
    self.assertEqual(summary.failed_count, 1)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_converter -v`
Expected: FAIL because conversion helpers are missing.

**Step 3: Write minimal implementation**

```python
def convert_file(task: ConversionTask, ffmpeg_path: Path | None = None) -> ConversionResult:
    completed = subprocess.run([...], capture_output=True, text=True)
    return ConversionResult(...)
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_converter -v`
Expected: PASS for the execution and error-reporting cases.

### Task 3: Add failing tests for ffmpeg discovery and real AMR smoke path

**Files:**
- Modify: `tests/test_converter.py`
- Modify: `tests/test_helpers.py`
- Modify: `amr_to_mp3/converter.py`
- Test: `tests/test_converter.py`

**Step 1: Write the failing tests**

```python
def test_resolve_ffmpeg_uses_env_override(self):
    with patch.dict(os.environ, {"AMR_TO_MP3_FFMPEG": str(fake_ffmpeg)}):
        self.assertEqual(resolve_ffmpeg_binary(), fake_ffmpeg)

def test_real_ffmpeg_smoke_conversion(self):
    if shutil.which("ffmpeg") is None:
        self.skipTest("ffmpeg not installed")
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_converter -v`
Expected: FAIL until ffmpeg resolution exists.

**Step 3: Write minimal implementation**

```python
def resolve_ffmpeg_binary() -> Path:
    if env_override:
        return Path(env_override)
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_converter -v`
Expected: PASS, including the smoke conversion when local ffmpeg is available.

### Task 4: Build the Tkinter desktop GUI

**Files:**
- Create: `amr_to_mp3/gui.py`
- Create: `amr_to_mp3/__main__.py`
- Modify: `amr_to_mp3/converter.py`
- Test: manual smoke on Windows; import-level validation locally

**Step 1: Write the failing test**

Because the current macOS Python runtime has no `_tkinter`, use an import-level smoke check instead of a widget test:

```python
def test_gui_module_can_be_imported_when_tkinter_exists():
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_converter -v`
Expected: FAIL until GUI entry points exist.

**Step 3: Write minimal implementation**

```python
class ConverterApp:
    def run_conversion(self) -> None:
        thread = Thread(target=self._convert_worker, daemon=True)
        thread.start()
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_converter -v`
Expected: PASS for import-level checks. Manual Windows GUI run remains documented.

### Task 5: Add README and Windows packaging instructions

**Files:**
- Create: `README.md`
- Create: `build/windows/amr_to_mp3.spec`
- Create: `build/windows/build.ps1`

**Step 1: Write the failing test**

Use a documentation checklist rather than an automated test:
- README includes run steps
- README includes build steps
- README includes dependency explanation
- README explains ffmpeg bundling for Windows

**Step 2: Verify the checklist fails**

Run: `test -f README.md`
Expected: file missing.

**Step 3: Write minimal implementation**

Add concise runtime and build documentation plus a PyInstaller spec and PowerShell build helper.

**Step 4: Verify it passes**

Run: `test -f README.md && test -f build/windows/amr_to_mp3.spec && test -f build/windows/build.ps1`
Expected: command exits 0.

### Task 6: Run verification before completion

**Files:**
- Modify: `README.md`
- Modify: `tests/test_converter.py`
- Modify: any touched source files if verification reveals issues

**Step 1: Run the full verification commands**

```bash
python3 -m unittest discover -s tests -v
python3 -m amr_to_mp3 --help
```

**Step 2: Run a real conversion smoke flow**

```bash
python3 -m unittest tests.test_converter.ConverterSmokeTests.test_real_ffmpeg_smoke_conversion -v
```

**Step 3: Fix anything that fails**

Keep the implementation minimal. Do not expand scope beyond the original feature set.

**Step 4: Record risks**

Document the local limitation: current macOS Python runtime lacks `_tkinter`, so GUI interaction must be validated on Windows or on a Python build with Tk support.
