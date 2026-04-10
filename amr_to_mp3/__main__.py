from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).resolve().parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


def _write_line(stream: object, message: str) -> None:
    if callable(getattr(stream, "write", None)):
        print(message, file=stream)


def _append_probe_log(message: str) -> None:
    log_path = os.environ.get("AMR_TO_MP3_PROBE_LOG")
    if not log_path:
        return

    try:
        path = Path(log_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{message}\n")
    except OSError:
        return


def _load_launch_gui():
    if __package__:
        from .gui import launch_gui

        return launch_gui

    _ensure_project_root_on_path()
    from amr_to_mp3.gui import launch_gui

    return launch_gui


def _load_resolve_ffmpeg_binary():
    if __package__:
        from .converter import resolve_ffmpeg_binary

        return resolve_ffmpeg_binary

    _ensure_project_root_on_path()
    from amr_to_mp3.converter import resolve_ffmpeg_binary

    return resolve_ffmpeg_binary


def _probe_ffmpeg_binary() -> str:
    _append_probe_log("probe: resolving ffmpeg")
    resolve_ffmpeg_binary = _load_resolve_ffmpeg_binary()
    ffmpeg_path = resolve_ffmpeg_binary()
    _append_probe_log(f"probe: ffmpeg_path={ffmpeg_path}")

    command = [str(ffmpeg_path), "-version"]
    if ffmpeg_path.suffix.lower() == ".py":
        command.insert(0, sys.executable)
    _append_probe_log(f"probe: command={' '.join(command)}")

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    _append_probe_log(f"probe: return_code={completed.returncode}")
    if output:
        _append_probe_log(f"probe: output={output.splitlines()[0]}")
    if completed.returncode != 0:
        message = output or f"ffmpeg probe failed with exit code {completed.returncode}"
        raise RuntimeError(message)

    first_line = output.splitlines()[0] if output else ""
    return f"ffmpeg ok: {ffmpeg_path}\n{first_line}".rstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m amr_to_mp3",
        description="AMR to MP3 desktop converter. Launches the GUI by default.",
    )
    parser.add_argument("--probe-ffmpeg", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.probe_ffmpeg:
            _append_probe_log("probe: start")
            probe_output = _probe_ffmpeg_binary()
            _write_line(sys.stdout, probe_output)
            _append_probe_log("probe: success")
            return 0

        launch_gui = _load_launch_gui()
        launch_gui()
    except Exception as exc:
        if args.probe_ffmpeg:
            _append_probe_log(f"probe: exception={type(exc).__name__}: {exc}")
            _write_line(sys.stderr, str(exc))
            return 1

        if isinstance(exc, RuntimeError):
            _write_line(sys.stderr, str(exc))
            return 1

        raise

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
