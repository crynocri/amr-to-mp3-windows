from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .gui import launch_gui


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="python -m amr_to_mp3",
        description="AMR to MP3 desktop converter. Launches the GUI by default.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)

    try:
        launch_gui()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
