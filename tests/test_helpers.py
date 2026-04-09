from __future__ import annotations

import os
import stat
import textwrap
from pathlib import Path


def write_minimal_amr(path: Path) -> Path:
    path.write_bytes(b"#!AMR\n\x04" + (b"\x00" * 12))
    return path


def write_fake_ffmpeg(path: Path, fail_names: tuple[str, ...] = ()) -> Path:
    script = textwrap.dedent(
        f"""\
        #!/usr/bin/env python3
        import pathlib
        import sys

        FAIL_NAMES = {tuple(fail_names)!r}

        def main() -> int:
            args = sys.argv[1:]
            input_path = None
            output_path = None

            for index, value in enumerate(args):
                if value == "-i" and index + 1 < len(args):
                    input_path = pathlib.Path(args[index + 1])

            if args:
                output_path = pathlib.Path(args[-1])

            if input_path is None or output_path is None:
                print("invalid invocation", file=sys.stderr)
                return 2

            if input_path.name in FAIL_NAMES:
                print(f"failed for {{input_path.name}}", file=sys.stderr)
                return 1

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"ID3" + input_path.name.encode("utf-8"))
            return 0

        raise SystemExit(main())
        """
    )
    path.write_text(script, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path
