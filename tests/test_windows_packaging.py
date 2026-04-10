from __future__ import annotations

import unittest
from pathlib import Path


class WindowsPackagingConfigTests(unittest.TestCase):
    def test_workflow_uses_real_chocolatey_ffmpeg_binary(self) -> None:
        workflow = Path(".github/workflows/windows-package.yml").read_text(encoding="utf-8")

        self.assertNotIn(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe", workflow)
        self.assertIn(r"C:\ProgramData\chocolatey\lib\ffmpeg", workflow)

    def test_workflow_smoke_tests_bundled_ffmpeg_after_packaging(self) -> None:
        workflow = Path(".github/workflows/windows-package.yml").read_text(encoding="utf-8")

        self.assertIn(r"dist\AMRToMP3\_internal\ffmpeg.exe", workflow)
        self.assertIn("-version", workflow)

    def test_build_script_validates_bundled_ffmpeg_before_packaging(self) -> None:
        build_script = Path("build/windows/build.ps1").read_text(encoding="utf-8")

        self.assertIn("$bundledFfmpeg", build_script)
        self.assertIn("-version", build_script)


if __name__ == "__main__":
    unittest.main()
