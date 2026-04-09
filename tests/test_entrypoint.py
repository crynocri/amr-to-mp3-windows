from __future__ import annotations

import contextlib
import io
import unittest
from unittest.mock import patch

from amr_to_mp3.__main__ import main


class EntryPointTests(unittest.TestCase):
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
            with patch("amr_to_mp3.__main__.launch_gui", side_effect=RuntimeError("Tkinter is unavailable")):
                exit_code = main([])

        self.assertEqual(exit_code, 1)
        self.assertIn("Tkinter is unavailable", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
