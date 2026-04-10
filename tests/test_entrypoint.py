from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from amr_to_mp3.__main__ import main


class EntryPointTests(unittest.TestCase):
    def test_main_script_runs_without_package_context(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        script_path = project_root / "amr_to_mp3" / "__main__.py"

        completed = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            cwd=project_root,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("AMR to MP3", completed.stdout)

    def test_main_help_exits_cleanly(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as exit_context:
                main(["--help"])

        self.assertEqual(exit_context.exception.code, 0)
        self.assertIn("AMR to MP3", stdout.getvalue())

    def test_main_reports_missing_tkinter_cleanly(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with patch("amr_to_mp3.__main__._load_launch_gui", side_effect=RuntimeError("Tkinter is unavailable")):
                exit_code = main([])

        self.assertEqual(exit_code, 1)
        self.assertIn("Tkinter is unavailable", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
