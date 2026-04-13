from __future__ import annotations

import unittest
from pathlib import Path


class WindowsPackagingConfigTests(unittest.TestCase):
    def test_installer_outputs_setup_exe(self) -> None:
        installer = Path("build/windows/installer.iss").read_text(encoding="utf-8")

        self.assertIn("OutputBaseFilename=AMRToMP3-Setup", installer)
        self.assertIn('Parameters: "install-shell"', installer)
        self.assertIn('Parameters: "uninstall-shell"', installer)

    def test_workflow_uses_real_chocolatey_ffmpeg_binary(self) -> None:
        workflow = Path(".github/workflows/windows-package.yml").read_text(encoding="utf-8")

        self.assertNotIn(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe", workflow)
        self.assertIn(r"C:\ProgramData\chocolatey\lib\ffmpeg", workflow)

    def test_workflow_runs_go_build_pipeline(self) -> None:
        workflow = Path(".github/workflows/windows-package.yml").read_text(encoding="utf-8")

        self.assertIn("actions/setup-go", workflow)
        self.assertIn("go test ./...", workflow)
        self.assertIn(r"build\windows\build.ps1", workflow)
        self.assertIn(r"scripts\windows\assert-context-menu.ps1", workflow)
        self.assertIn(r"scripts\windows\smoke-convert.ps1", workflow)
        self.assertIn("install-shell", workflow)
        self.assertIn("uninstall-shell", workflow)
        self.assertIn("AMRToMP3-Setup.exe", workflow)

    def test_build_script_uses_go_and_inno_setup(self) -> None:
        build_script = Path("build/windows/build.ps1").read_text(encoding="utf-8")

        self.assertIn("$bundledFfmpeg", build_script)
        self.assertIn("-version", build_script)
        self.assertIn("$versionOutput = & $bundledFfmpeg -version 2>&1", build_script)
        self.assertIn("go build", build_script)
        self.assertIn("iscc", build_script)


if __name__ == "__main__":
    unittest.main()
