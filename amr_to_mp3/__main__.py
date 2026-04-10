from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


def _load_launch_gui():
    if __package__:
        from .gui import launch_gui

        return launch_gui

    project_root = Path(__file__).resolve().parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

    from amr_to_mp3.gui import launch_gui

    return launch_gui


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="python -m amr_to_mp3",
        description="AMR to MP3 desktop converter. Launches the GUI by default.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)

    try:
        launch_gui = _load_launch_gui()
        launch_gui()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
