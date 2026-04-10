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
    def test_main_probe_ffmpeg_skips_print_when_stdout_is_not_writable(self) -> None:
        class BadStdout:
            def flush(self) -> None:
                return None

        with patch("amr_to_mp3.__main__._probe_ffmpeg_binary", return_value="ffmpeg ok"):
            with patch.object(sys, "stdout", BadStdout()):
                exit_code = main(["--probe-ffmpeg"])

        self.assertEqual(exit_code, 0)

    def test_probe_ffmpeg_uses_devnull_stdin(self) -> None:
        with patch("amr_to_mp3.__main__._load_resolve_ffmpeg_binary", return_value=lambda: Path("ffmpeg.exe")):
            with patch("subprocess.run") as run:
                run.return_value = subprocess.CompletedProcess(
                    ["ffmpeg.exe", "-version"],
                    0,
                    stdout="ffmpeg version test\n",
                    stderr="",
                )

                output = main(["--probe-ffmpeg"])

        self.assertEqual(output, 0)
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_main_probe_ffmpeg_exits_without_launching_gui(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            with patch("amr_to_mp3.__main__._probe_ffmpeg_binary", return_value="ffmpeg ok", create=True):
                with patch("amr_to_mp3.__main__._load_launch_gui") as launch_gui:
                    exit_code = main(["--probe-ffmpeg"])

        self.assertEqual(exit_code, 0)
        self.assertIn("ffmpeg ok", stdout.getvalue())
        launch_gui.assert_not_called()

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
