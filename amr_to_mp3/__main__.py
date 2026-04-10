from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).resolve().parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


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
    resolve_ffmpeg_binary = _load_resolve_ffmpeg_binary()
    ffmpeg_path = resolve_ffmpeg_binary()

    command = [str(ffmpeg_path), "-version"]
    if ffmpeg_path.suffix.lower() == ".py":
        command.insert(0, sys.executable)

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
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
            print(_probe_ffmpeg_binary())
            return 0

        launch_gui = _load_launch_gui()
        launch_gui()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
